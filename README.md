<div align="center" markdown>
<img src="https://i.imgur.com/vfDDYqh.png"/>

# Diff Merge Two Images Projects

<p align="center">
  <a href="#Overview">Overview</a> •
  <a href="#How-To-Use">How To Use</a>
</p>


[![](https://img.shields.io/badge/supervisely-ecosystem-brightgreen)](https://ecosystem.supervise.ly/apps/diff-merge-images-projects)
[![](https://img.shields.io/badge/slack-chat-green.svg?logo=slack)](https://supervise.ly/slack)
![GitHub release (latest SemVer)](https://img.shields.io/github/v/release/supervisely-ecosystem/diff-merge-images-projects)
[![views](https://app.supervise.ly/public/api/v3/ecosystem.counters?repo=supervisely-ecosystem/diff-merge-images-projects&counter=views&label=views)](https://supervise.ly)
[![used by teams](https://app.supervise.ly/public/api/v3/ecosystem.counters?repo=supervisely-ecosystem/diff-merge-images-projects&counter=downloads&label=used%20by%20teams)](https://supervise.ly)
[![runs](https://app.supervise.ly/public/api/v3/ecosystem.counters?repo=supervisely-ecosystem/diff-merge-images-projects&counter=runs&label=runs)](https://supervise.ly)

</div>

## Overview

Visually compare and merge two images projects: datasets / images / image tags / labels / image metadata. Define how to merge them and how to resolve conflicts. 

<img src="https://i.imgur.com/qTnXLaC.png"/>

## How To Use

**Step 1:** Add app to your team from Ecosystem if it is not there

**Step 2:** Please, firstly use [`Diff Merge Project Meta`](https://ecosystem.supervise.ly/apps/diff-merge-project-meta) app to merge project metas: classes and tags. As a result empty project with merged classes and tags will be created. This project should be used as a result project for current application. 

**Step 2:** Run app from the `Apps` page of current team

<img src="https://i.imgur.com/QRYME1U.png" width="500px"/>

**Step 3:** Explore comparison tables, define merge options and press `Run` button.

**Step 4:** New project is created. Information about input projects is saved in `custom data` of created project. For example:

```json
{
  "project1": {
    "id": 1436,
    "name": "lemons_annotated"
  },
  "project2": {
    "id": 1455,
    "name": "kiwi_annotated"
  }
}
```

<img src="https://i.imgur.com/TR070VM.png"/>

**Step 4:** Task is created in `Application Sessions`. 
