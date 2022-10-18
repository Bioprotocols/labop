---
layout: default
title: "Materials"
permalink: /materials/
---

# Presentations
{% assign image_files = site.static_files | where: "presentation", true %}
{% for myimage in image_files %}
    {% assign description = site.data.data[0].presentations[myimage.name].description %}
  - [{{ myimage.name }}]({{ myimage.path }}): {{ description }}
{% endfor %}

# Articles
