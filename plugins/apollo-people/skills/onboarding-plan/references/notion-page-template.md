# Notion Page Template — Onboarding Plan

Exact Notion enhanced markdown for the onboarding plan page. Variable sections are marked with [VARIABLE]. Everything else reproduces exactly — callout colors, toggle syntax, indentation (tabs), icon paths.

______________________________________________________________________

```
<callout icon="/icons/list-indent_purple.svg" color="gray_bg">
	<details>
	<summary>**Table of contents**</summary>
		<table_of_contents color="gray"/>
	</details>
</callout>
---
<callout icon="/icons/user_purple.svg" color="blue_bg">
	## **Manager Instructions** {toggle="true"}
		- [ ] Customize the plan drafted by Claude
		- [ ] Review the plan with the new hire during your first 1:1
</callout>
<callout icon="/icons/follow_purple.svg" color="green_bg">
	## **New Hire Instructions** {toggle="true"}
		- [ ] Star this page for quick access during onboarding
		- [ ] Check off items as you complete them
		- [ ] Capture questions and blockers for your manager
</callout>
---
## Overview {toggle="true" color="purple_bg"}
	<table>
	<colgroup>
	<col width="215.5">
	<col color="purple_bg" width="856.5">
	</colgroup>
	<tr>
	<td>**New Hire:**</td>
	<td>@name</td>
	</tr>
	<tr>
	<td>**Role:**</td>
	<td>[VARIABLE: role title]</td>
	</tr>
	<tr>
	<td>**Manager:**</td>
	<td>@manager</td>
	</tr>
	<tr>
	<td>People Business Partner</td>
	<td>@PBP</td>
	</tr>
	<tr>
	<td>**Onboarding Buddy:**</td>
	<td>@buddy</td>
	</tr>
	<tr>
	<td>**Start Date:**</td>
	<td>@date</td>
	</tr>
	<tr>
	<td>**Job Description or Role Scorecard:**</td>
	<td></td>
	</tr>
	<tr>
	<td>Your Role and how it connects to Apollo's Success:</td>
	<td>3–5 bullet statements tied to company priorities and metrics</td>
	</tr>
	</table>
---
## 15/30/60 Day Objectives {toggle="true" color="gray_bg"}
	<callout icon="/icons/info-alternate_gray.svg" color="orange_bg">
		A place for you and your manager to define objectives for your first 60 days.
	</callout>
	### 15 Day Objectives
	[VARIABLE: generated objectives as tab-indented checklist items with success indicators as further-indented sub-bullets]
	### 30 Day Objectives
	[VARIABLE: same]
	### 60 Day Objectives
	[VARIABLE: same]
---
## Learning & Development Program {toggle="true" color="gray_bg"}
	<callout icon="/icons/info-alternate_gray.svg" color="orange_bg">
		All new hires must complete the [**New Hire Orientation Program**](https://apolloio.sana.ai/program/f3b71a34-7970-4d30-93d3-fca74c61653f) which is assigned in [Sana](https://apolloio.sana.ai/) within their first 60 days. In the program, you will learn about culture, strategy, industry knowledge, hands-on product, and leadership essentials.
	</callout>
---
## People to meet {toggle="true" color="gray_bg"}
	[VARIABLE: checklist items grouped under bold phase headers]
---
## Tactical {toggle="true" color="gray_bg"}
	### Meetings/Rituals
	- [ ] 
	### Slack Channels
	- [ ] **ai-native-learning**
	- [ ] **competitors**
	- [ ] **marketing**
	- [ ] **engineering**
	### Team Resources
	[VARIABLE: linked resources if provided, otherwise omit this heading entirely]
```

______________________________________________________________________

## Indentation rules

All content inside a toggle must be tab-indented. Example for objectives:

```
## 15/30/60 Day Objectives {toggle="true" color="gray_bg"}
	<callout icon="/icons/info-alternate_gray.svg" color="orange_bg">
		A place for you and your manager to define objectives for your first 60 days.
	</callout>
	### 15 Day Objectives
	- [ ] Objective text here
		- Success Indicators: What progress looks like
	- [ ] Second objective
		- Success Indicators: What progress looks like
```

Same rule applies to People to meet and Tactical — everything inside the toggle gets one tab of indentation.
