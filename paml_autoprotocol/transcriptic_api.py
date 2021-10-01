import json
import os
import requests
import time
import transcriptic

from datetime import datetime

class TranscripticException(Exception):
    pass

class TranscripticEnvironmentException(Exception):
    pass


class TranscripticConfig():
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

    def __init__(self, email: str, token: str, user_id: str, organization_id: str, project_id: str) -> None:
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
            "organization_id":  self.organization_id,
            "token": self.token,
            "user_id": self.user_id
            }

    @staticmethod
    def from_environment():
        def get_env_else_error(var):
            res = os.environ.get(var)
            if res is None:
                raise TranscripticEnvironmentException(f"Environment variable '{var}' is unset")
            return res
        email = get_env_else_error("_TRANSCRIPTIC_EMAIL")
        token = get_env_else_error("_TRANSCRIPTIC_TOKEN")
        user = get_env_else_error("_TRANSCRIPTIC_USER_ID")
        org = get_env_else_error("_TRANSCRIPTIC_ORGANIZATION_ID")
        proj = get_env_else_error("_TRANSCRIPTIC_PROJECT_ID")
        return TranscripticConfig(email, token, user, org, proj)

class TranscripticProtocol():
    def __init__(self, protocol):
        self.protocol = protocol
        self.id = protocol["id"]
        self.name = protocol["name"]

class TranscripticAPI():

    @property
    def protocol_make_containers(self) -> TranscripticProtocol:
        return self._protocol_make_containers

    def __init__(self, out_dir: str, cfg: TranscripticConfig = None) -> None:
        self.out_dir = out_dir
        self.cfg = TranscripticConfig.from_environment() if cfg is None else cfg

        self._protocol_name_map = {}
        ps = self.query_all_protocols()
        for p in ps:
            tp = TranscripticProtocol(p)
            self._protocol_name_map[p["name"]] = tp

        self._protocol_make_containers = self._name_to_protocol("MakeContainers")
        
    def _name_to_protocol(self, name: str):
        res = self._protocol_name_map.get(name)
        if res is None:
            raise TranscripticException(f"Failed to find '{name}' in protocol name map")
        return res
        
    def _build_headers(self):
        return {"X-User-Email": self.cfg.email,  # user-account-email
                "X-User-Token": self.cfg.token,  # Regular-mode API key
                "Content-Type": "application/json",
                "Accept": "application/json"}

    def _build_query_protocols(self):
        return ("https://secure.transcriptic.com/{}/protocols.json".format(self.cfg.organization_id),
                self._build_headers())


    def query_all_protocols(self):
        """
        Get all protocols
        """
        (url, headers) = self._build_query_protocols()
        print(headers)
        response = requests.get(url, headers=headers)
        return json.loads(response.content)

    # TODO
    def make_containers(self, containers, title = "make_containers"):
        params = {
            "parameters": {
                "containers": containers
            }
        }
        # TODO verify this request then enable sending
        # response = self.submit_to_transcriptic(self.make_containers, params, title)
        return None

    def get_transcriptic_connection(self):
        """Connect (without validation) to Transcriptic.com"""
        try:
            return transcriptic.Connection(**self.cfg.to_dict())
        except Exception:
            raise


    def submit_to_transcriptic(self,
                               protocol: TranscripticProtocol,
                               params,
                               title,
                               test_mode=True):
        """Submit to transcriptic and record response"""

        launch_request_id = None
        launch_protocol = None

        try:
            conn = self.get_transcriptic_connection()
        except Exception as exc:
            raise TranscripticException(exc)

        try:
            launch_request = self._create_launch_request(params,
                                                    title,
                                                    test_mode=test_mode,
                                                    out_dir=self.out_dir)
            try:
                launch_protocol = conn.launch_protocol(launch_request,
                                                       protocol_id=protocol.id)
            except Exception as exc:
                raise TranscripticException(exc)
            launch_request_id = launch_protocol["id"]
        except Exception as exc:
            raise TranscripticException(exc)

        # Delay needed because it takes Transcriptic a few seconds to
        # complete launch_protocol()
        time.sleep(30)

        request_response = {}
        try:
            req_title = "{}_{}_{}".format(
                datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%ST%f'),
                title,
                protocol.name
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
                test_mode=test_mode)
            return request_response

        except Exception as exc:
            raise TranscripticException(exc)

    def _create_launch_request(self, params, local_name, bsl=1, test_mode=True):
        """Creates launch_request from input params"""
        params_dict = dict()
        params_dict["launch_request"] = params
        params_dict["launch_request"]["bsl"] = bsl
        params_dict["launch_request"]["test_mode"] = test_mode

        with open(os.path.join(self.out_dir, 'launch_request_{}.json'.format(local_name)), 'w') as lr:
            json.dump(params_dict, lr, sort_keys=True,
                    indent=2, separators=(',', ': '))
        return json.dumps(params_dict)


    #@retry(stop=stop_after_delay(70), wait=wait_exponential(multiplier=1, max=16))
    def __submit_launch_request(self, conn, launch_request_id, protocol_id=None,
                                project_id=None, title=None, test_mode=True):
        try:
            print("Launching: launch_request_id = " + launch_request_id)
            print("Launching: protocol_id = " + protocol_id)
            print("Launching: project_id = " + project_id)
            print("Launching: title = " + title)
            print("Launching: test_mode = " + str(test_mode))
            lr = conn.submit_launch_request(launch_request_id,
                                            protocol_id=protocol_id,
                                            project_id=project_id,
                                            title=title,
                                            test_mode=test_mode)
            return lr
        except Exception as exc:
            raise TranscripticException(exc)

