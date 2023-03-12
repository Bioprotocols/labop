import json
import os
import requests
import time
import transcriptic

from datetime import datetime
import requests
from requests_html import HTMLSession


import logging

l = logging.getLogger(__file__)
l.setLevel(logging.ERROR)


class StrateosException(Exception):
    pass


class StrateosEnvironmentException(Exception):
    pass


class StrateosConfig:
    @property
    def email(self) -> str:
        return self._email

    @property
    def token(self) -> str:
        return self._token

    @property
    def user_id(self) -> str:
        return self._user_id

    @property
    def organization_id(self) -> str:
        return self._organization_id

    @property
    def project_id(self) -> str:
        return self._project_id

    def __init__(
        self,
        email: str,
        token: str,
        user_id: str,
        organization_id: str,
        project_id: str,
    ) -> None:
        self._email = email
        self._token = token
        self._user_id = user_id
        self._organization_id = organization_id
        self._project_id = project_id

    def to_dict(self):
        return {
            "analytics": True,
            "api_root": "https://secure.transcriptic.com",
            "email": self.email,
            "feature_groups": [],
            "organization_id": self.organization_id,
            "token": self.token,
            "user_id": self.user_id,
        }

    @staticmethod
    def from_file(cfg_file):
        def get_file_else_error(cfg, var):
            res = cfg[var] if var in cfg else None
            if res is None:
                raise StrateosEnvironmentException(
                    f"Configuration variable '{var}' is unset"
                )
            return res

        with open(cfg_file, "r") as tx_cfg_file:
            # Lab Configuration
            tx_cfg = json.load(tx_cfg_file)
            email = get_file_else_error(tx_cfg, "email")
            token = get_file_else_error(tx_cfg, "token")
            user = get_file_else_error(tx_cfg, "email")
            org = get_file_else_error(tx_cfg, "organization_id")
            project_id = get_file_else_error(tx_cfg, "project_id")
            return StrateosConfig(email, token, user, org, project_id)

    @staticmethod
    def from_environment():
        def get_env_else_error(var):
            res = os.environ.get(var)
            if res is None:
                raise StrateosEnvironmentException(
                    f"Environment variable '{var}' is unset"
                )
            return res

        email = get_env_else_error("_TRANSCRIPTIC_EMAIL")
        token = get_env_else_error("_TRANSCRIPTIC_TOKEN")
        user = get_env_else_error("_TRANSCRIPTIC_USER_ID")
        org = get_env_else_error("_TRANSCRIPTIC_ORGANIZATION_ID")
        proj = get_env_else_error("_TRANSCRIPTIC_PROJECT_ID")
        return StrateosConfig(email, token, user, org, proj)


class StrateosProtocol:
    def __init__(self, protocol):
        self.protocol = protocol
        self.id = protocol["id"]
        self.name = protocol["name"]


class StrateosAPI:
    @property
    def protocol_make_containers(self) -> StrateosProtocol:
        return self._protocol_make_containers

    def __init__(self, out_dir: str = "./", cfg: StrateosConfig = None) -> None:
        self.out_dir = out_dir
        if not os.path.exists(self.out_dir):
            os.mkdir(self.out_dir)

        self.cfg = StrateosConfig.from_environment() if cfg is None else cfg

        self._protocol_name_map = {}
        ps = self.query_all_protocols()
        for p in ps:
            tp = StrateosProtocol(p)
            self._protocol_name_map[p["name"]] = tp

        self._protocol_make_containers = self._name_to_protocol("MakeContainers")

    def _name_to_protocol(self, name: str):
        res = self._protocol_name_map.get(name)
        if res is None:
            raise StrateosException(f"Failed to find '{name}' in protocol name map")
        return res

    def _build_headers(self):
        return {
            "X-User-Email": self.cfg.email,  # user-account-email
            "X-User-Token": self.cfg.token,  # Regular-mode API key
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _build_query_protocols(self):
        return (
            "https://secure.transcriptic.com/{}/protocols.json".format(
                self.cfg.organization_id
            ),
            self._build_headers(),
        )

    def query_all_protocols(self):
        """
        Get all protocols
        """
        (url, headers) = self._build_query_protocols()
        # l.debug(headers)
        response = requests.get(url, headers=headers)
        return json.loads(response.content)

    # TODO
    def make_containers(self, containers, title="make_containers", test_mode=True):
        params = {"parameters": {"containers": containers}}
        # TODO verify this request then enable sending
        response = self.submit_to_strateos(
            self._protocol_make_containers, params, title
        )

        container_ids = {x["name"]: x["container_id"] for x in response["refs"]}

        return container_ids

    def get_strateos_connection(self):
        """Connect (without validation) to Strateos.com"""
        try:
            return transcriptic.Connection(**self.cfg.to_dict())
        except Exception:
            raise

    def submit_to_strateos(
        self, protocol: StrateosProtocol, params, title, test_mode=True
    ):
        """Submit to Strateos and record response"""

        launch_request_id = None
        launch_protocol = None

        try:
            conn = self.get_strateos_connection()
        except Exception as exc:
            raise StrateosException(exc)

        try:
            launch_request = self._create_launch_request(
                params, title, test_mode=test_mode
            )
            try:
                launch_protocol = conn.launch_protocol(
                    launch_request, protocol_id=protocol.id
                )
            except Exception as exc:
                raise StrateosException(exc)
            launch_request_id = launch_protocol["id"]
        except Exception as exc:
            raise StrateosException(exc)

        # Delay needed because it takes Strateos a few seconds to
        # complete launch_protocol()
        time.sleep(30)

        request_response = {}
        try:
            req_title = "{}_{}_{}".format(
                datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%ST%f"), title, protocol.name
            )

            # req_title = "{}-{}".format(
            #    robj.get_attr('name'),
            #    arrow.utcnow().format('YYYY-MM-DDThh:mm:ssTZD'))
            # Retry submission up to timeout, with exponential backoff
            request_response = self.__submit_launch_request(
                conn,
                launch_request_id,
                protocol_id=protocol.id,
                project_id=self.cfg.project_id,
                title=req_title,
                test_mode=test_mode,
            )
            return request_response

        except Exception as exc:
            raise StrateosException(exc)

    def _create_launch_request(self, params, local_name, bsl=1, test_mode=True):
        """Creates launch_request from input params"""
        params_dict = dict()
        params_dict["launch_request"] = params
        params_dict["launch_request"]["bsl"] = bsl
        params_dict["launch_request"]["test_mode"] = test_mode

        with open(
            os.path.join(self.out_dir, "launch_request_{}.json".format(local_name)), "w"
        ) as lr:
            json.dump(params_dict, lr, sort_keys=True, indent=2, separators=(",", ": "))
        return json.dumps(params_dict)

    # @retry(stop=stop_after_delay(70), wait=wait_exponential(multiplier=1, max=16))
    def __submit_launch_request(
        self,
        conn,
        launch_request_id,
        protocol_id=None,
        project_id=None,
        title=None,
        test_mode=True,
    ):
        try:
            l.debug("Launching: launch_request_id = " + launch_request_id)
            l.debug("Launching: protocol_id = " + protocol_id)
            l.debug("Launching: project_id = " + project_id)
            l.debug("Launching: title = " + title)
            l.debug("Launching: test_mode = " + str(test_mode))
            lr = conn.submit_launch_request(
                launch_request_id,
                protocol_id=protocol_id,
                project_id=project_id,
                title=title,
                test_mode=test_mode,
            )
            return lr
        except Exception as exc:
            raise StrateosException(exc)

    def resolve_resource(self, resource):
        types = resource.types
        resolutions = {}
        for type in types:
            try:
                session = HTMLSession()
                response = session.get(type)
                meta = response.html.find("meta")
                properties = [
                    x.attrs for x in response.html.find("meta") if "property" in x.attrs
                ]
                [title] = [
                    x["content"] for x in properties if x["property"] == "og:title"
                ]
            except requests.exceptions.RequestException as e:
                l.debug(e)

        conn = self.get_strateos_connection()
        results = conn.resources(resource)["results"]
        return results
