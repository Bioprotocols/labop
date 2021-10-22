# PAML Notebooks

The notebooks in this directory demonstrate several use cases for the PAML language, including:

- [paml_demo.ipynb](paml_demo.ipynb): Demonstrates building a protocol from a list of PAML API instructions, visualizing the protocol, simulated protocol execution,and serialization to Markdown.
- [Autoprotocol.ipynb](Autoprotocol.ipynb): Demonstrate converting and submitting protocol from PAML to Autoprotocol for execution at Strateos
- [markdown.ipynb](markdown.ipynb): Convert protocol to Markdown.

# Dependencies

- [container_api](https://github.com/rpgoldman/container-ontology): Needed to resolve container specifications to a list of possible container types.  Used by importing as follows:  
  ```
  from container_api.client_api import matching_containers, strateos_id
  
  possible_container_types = matching_containers(spec)
  possible_short_names = [strateos_id(x) for x in possible_container_types]
  ```