<div align="center" markdown>

<img src="https://user-images.githubusercontent.com/106374579/183656137-70a107a9-4497-40be-8e21-1a2c9d8d98f1.png"/>

# Diff Merge Two Images Projects

<p align="center">
  <a href="#Overview">Overview</a> •
  <a href="#How-To-Use">How To Use</a>
</p>


[![](https://img.shields.io/badge/supervisely-ecosystem-brightgreen)](../../../../supervisely-ecosystem/diff-merge-images-projects)
[![](https://img.shields.io/badge/slack-chat-green.svg?logo=slack)](https://supervisely.com/slack)
![GitHub release (latest SemVer)](https://img.shields.io/github/v/release/supervisely-ecosystem/diff-merge-images-projects)
[![views](https://app.supervisely.com/img/badges/views/supervisely-ecosystem/diff-merge-images-projects.png)](https://supervisely.com)
[![runs](https://app.supervisely.com/img/badges/runs/supervisely-ecosystem/diff-merge-images-projects.png)](https://supervisely.com)

</div>

## Overview

Visually compare and merge two images projects: datasets / images / image tags / labels / image metadata. Define how to merge them and how to resolve conflicts. 

<img src="https://i.imgur.com/qTnXLaC.png"/>

## How To Use

**Step 1:** Add app to your team from Ecosystem if it is not there

**Step 2:** Please, firstly use [`Diff Merge Project Meta`](../../../../supervisely-ecosystem/diff-merge-project-meta) app to merge project metas: classes and tags. As a result empty project with merged classes and tags will be created. This project should be used as a result project for current application. 

**Step 2:** Run app from the `Apps` page of current team. Choose two projects to compare and merge

<img src="https://i.imgur.com/WkLZ05w.png" width="500px"/>

**Step 3:** Explore comparison table, define merge options and press `Run` button.

**Step 4:** See warnings and errors in app's logs

**Step 5:** Task is created in `Application Sessions`. 
