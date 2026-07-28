<!-- p:1 -->
## **Lost in Simulation: LLM-Simulated Users are Unreliable Proxies for** **Human Users in Agentic Evaluations**

<!-- p:2 -->
**Preethi Seshadri** [1] **Samuel Cahyawijaya** [2] **Ayomide Odumakinde** [2]

<!-- p:3 -->
**Sameer Singh** [1] **Seraphina Goldfarb-Tarrant** [2]

<!-- p:4 -->
1UC Irvine 2Cohere

<!-- p:5 -->
{preethis, sameer}@uci.edu
{samuelcahyawijaya, ayomideodumakinde, seraphina}@cohere.com

<!-- p:6 -->
**Abstract**

<!-- p:7 -->
Agentic benchmarks increasingly rely on LLMsimulated users to scalably evaluate agent performance, yet the robustness, validity, and
fairness of this approach remain unexamined.
Through a user study with participants across
the United States, India, Kenya, and Nigeria,
we investigate whether LLM-simulated users
serve as reliable proxies for real human users
in evaluating agents on _τ_ -Bench retail tasks.
We find that user simulation lacks robustness,
with agent success rates varying up to 9 percentage points across different user LLMs. Furthermore, evaluations using simulated users exhibit systematic miscalibration, underestimating agent performance on challenging tasks and
overestimating it on moderately difficult ones.
African American Vernacular English (AAVE)
speakers experience consistently worse success
rates and calibration errors than Standard American English (SAE) speakers, with disparities
compounding significantly with age. We also
find simulated users to be a differentially effective proxy for different populations, performing
worst for AAVE and Indian English speakers.
Additionally, simulated users introduce conversational artifacts and surface different failure patterns than human users. These findings
demonstrate that current evaluation practices
risk misrepresenting agent capabilities across
diverse user populations and may obscure realworld deployment challenges.

<!-- p:8 -->
**1** **Introduction**

<!-- p:9 -->
AI agents designed to assist with everyday tasks
such as travel reservations, order management,
and appointment scheduling are becoming increasingly prevalent (Xie et al., 2024; Zhou et al., 2024;
CNBC, 2025), but present significant challenges
to effective evaluation. Agentic benchmarks have
needed to evolve beyond static question-answering
and other single-turn formats to capture the dynamic, multi-turn nature of real user interactions
(Chang et al., 2025; Deshpande et al., 2025). Many

<!-- p:10 -->
Figure 1: Conversational snippets between an agent and
simulated (top) vs. human user (bottom) on the same
task. Simulated users exhibit increased question-asking
and politeness compared to human users.

<!-- p:11 -->
recent works have proposed benchmarks that reflect
this shift and instead measure sustained, contextaware interaction (Barres et al., 2025; Shao et al.,
2025; Wang et al., 2025a; Xu et al., 2025; Yao et al.,
2025). These benchmarks improve complexity and
ecological validity over prior static evaluations by
requiring agents to demonstrate a range of capabilities, including conversing naturally and coherently with users, adhering to policies, following
instructions closely, and making appropriate tool
calls over multiple turns. To facilitate automated
and scalable evaluation, these benchmarks typically
simulate conversations between an LLM agent and
a user, where the “user” is an LLM (Ivey et al.,
2024; He et al., 2025; Mehri et al., 2025).

<!-- p:12 -->
While this approach reduces the cost and operational overhead of human evaluation, it raises
critical questions about the **robustness**, **validity**,
and **fairness** of user simulation. First, evaluations

<!-- p:13 -->
1

<!-- p:14 -->
typically rely on a single user simulation model,
yet results may vary across different user LLMs
( **robustness** ). Second, without validation with
actual users (Salaudeen et al., 2025), it remains
unclear whether interactions between agents and
LLM-simulated users accurately reflect and predict interactions between agents and real people
( **validity**, Figure 1). If simulated users systematically differ from actual users in their interaction
patterns (Yoon et al., 2024), benchmarks may provide a misleading picture of agent capabilities due
to _miscalibration_ (i.e., simulated results do not reliably predict real user outcomes).
Third, these evaluations often treat users as a
homogeneous group, overlooking variation in how
people communicate and interact with AI systems
(Haoyue and Cho, 2024; Liu et al., 2024; Bassignana et al., 2025). In practice, users differ widely in
their communication styles, linguistic backgrounds,
and cultural norms (Pawar et al., 2025; Qiu et al.,
2025). For example, even in a simple retail assistance scenario, users might vary along dimensions such as formality, verbosity, and politeness
norms—but it remains unclear how much this diversity meaningfully impacts agent performance
and task success (Truong et al., 2025). Without
further investigation, simulated users may approximate some populations better than others, resulting
in non-uniform calibration errors that advantage or
disadvantage certain user groups ( **fairness** ).
Despite the widespread adoption of user simulation, prior work has overlooked validation against
real human interactions in agentic benchmarks. In
this paper, we address this gap by conducting a
user study with participants from the United States,
India, Kenya, and Nigeria to directly evaluate user
simulation as a proxy for actual users. Specifically,
we ask the following questions:

<!-- p:15 -->
- **Robustness:** How consistent are agentic
evaluations across different user simulation
LLMs?

<!-- p:16 -->
- **Validity:** Do simulated users serve as reliable
proxies for real human users in agentic evaluations?

<!-- p:17 -->
- **Fairness:** How does human-agent performance vary across different user groups, and
does user simulation represent certain groups
better than others?

<!-- p:18 -->
Using _τ_ -Bench retail tasks (Yao et al., 2025) as
a case study, we find that user simulation lacks
robustness, and systematically misestimates perfor

<!-- p:19 -->
mance with human users by underestimating success on the most challenging tasks while overestimating outcomes on moderately difficult scenarios.
More critically, simulated users exhibit notable demographic biases and perform particularly poorly
as proxies for African American Vernacular English speakers, with disparities compounding with
age. Simulated users also introduce artificial conversational artifacts such as heightened questionasking and politeness (Figure 1). Together, these
findings call into question the validity of user simulation as a stand-alone evaluation paradigm and
underscore the need for more robust and fair approaches to agentic evaluation.

<!-- p:20 -->
**2** **Related Work**

<!-- p:21 -->
**User** **Simulation** **in** **Interactive** **Settings** Dou
et al. (2025) and Wang et al. (2025b) investigate
user simulation in tasks such as math tutoring and
daily planning, but primarily focus on conversational characteristics (e.g., politeness) and behavioral realism (e.g., Turing-style tests). Additionally, Dou et al. (2025) optimize alignment with
human ratings using simulated user profiles. Lu
et al. (2025) analyze simulation fidelity by measuring how accurately simulated users replicate human intermediate steps in real-world online shopping sessions, and find substantial deviations between simulated and actual user action sequences.
None of these works examine the robustness of
agentic evaluations across different user simulation
models, nor do they consider fairness implications
across different user groups. Finally, while Zhu
et al. (2025) study the outcome and task validity
of agentic benchmark results, they do not consider
the validity of user simulation.

<!-- p:22 -->
**Demographic Skews in NLP Datasets and Mod-**
**els** Several previous works highlight that datasets
and models exhibit systematic skews toward specific demographic perspectives. Research on annotator disagreement reveals that perceptions of
safety, offensiveness, and toxicity meaningfully
vary along demographic axes like race, gender,
and political affiliation (Sap et al., 2022; Lee
et al., 2023; Prabhakaran et al., 2024). These
patterns of disagreement reflect broader issues of
positionality—both Santy et al. (2023) and Lee
et al. (2024) show that NLP datasets and models
tend to align predominantly with Western, educated, and Anglosphere populations. Similarly,
LLMs have been found to reflect the opinions of

<!-- p:23 -->
2

<!-- p:24 -->
Western countries (Durmus et al., 2024; Cahyawijaya et al., 2025) as well as wealthy and liberal
groups (Santurkar et al., 2023), and align more
closely with White annotators than Black or Asian
groups on subjective tasks like politeness (Sun
et al., 2025). Attempts to broaden model inclusivity
through sociodemographic prompting have shown
mixed results, often failing to consistently improve
alignment or relying on harmful stereotypes (Durmus et al., 2024; Sun et al., 2025). Overall, our
work builds on this line of research by examining
demographic differences in agentic settings.

<!-- p:25 -->
**3** **Methodology**

<!-- p:26 -->
**3.1** **Benchmark Background**

<!-- p:27 -->
We use _τ_ -Bench (Yao et al., 2025) as the testbed
for our evaluations, since it is a well-known and
widely-adopted benchmark for agentic tool use. [1]

<!-- p:28 -->
The benchmark is designed to capture how well AI
agents perform in real-world, interactive customer
service scenarios. Each task involves collaboration
between an agent and a simulated user: the user
receives task instructions with specific objectives
that guide their conversation with the agent, while
the agent must use tool calling to interact with realistic databases, adhere to domain-specific policies,
and gather necessary information from the user.
The task is considered successful if (1) the final
database state is identical to the unique ground truth
outcome (i.e., the sequence of required actions) and
(2) the agent’s responses convey all necessary information requested in the task instructions, which is
evaluated automatically using substring matching
against ground truth annotations. In total, _τ_ -Bench
contains 115 retail tasks (e.g., modifying pending
orders or returning delivered orders) and 50 airline tasks (e.g., booking, modifying, or canceling
reservations).

<!-- p:29 -->
**3.2** **Benchmark Adaptation**

<!-- p:30 -->
We focus on _τ_ -Bench retail tasks to enable more
systematic coverage within a single domain. We
apply preprocessing steps to ensure that neither
simulated nor human users are influenced by identity and behavioral cues in the instructions when
completing tasks (see Appendix A.4).
Given the large number of retail tasks, we sample a subset based on difficulty to ensure balanced
coverage across task complexities. Since _τ_ -Bench

<!-- p:31 -->
1 _τ_ -Bench Leaderboard: [https://taubench.com/](https://taubench.com/#leaderboard)
[#leaderboard](https://taubench.com/#leaderboard)

<!-- p:32 -->
does not provide difficulty labels, we compute a
model-based notion of difficulty by running the
benchmark 5 times using GPT-4o as both the agent
and user LLMs and measuring the task success rate
over 5 runs (i.e., the percentage of times a given
task is completed successfully). With five evaluation runs per task, success rates naturally fall into
six discrete levels (0/5, 1/5, 2/5, 3/5, 4/5, 5/5 = 0%,
20%, 40%, 60%, 80%, 100%). We use GPT-4o
because it is used in the _τ_ -Bench paper and does
not exhibit contamination issues that newer models
face. [2] We then select 3 tasks for each difficulty
level (18 total) to balance response coverage per
task with breadth across difficulty levels.

<!-- p:33 -->
**3.3** **User Study**

<!-- p:34 -->
To assess whether LLM-simulated users serve as
effective proxies for real and diverse users, we conduct a user study with participants from the United
States, India, Kenya, and Nigeria. Since _τ_ -Bench
tasks are in English, we select countries with large
English-speaking populations that also provide geographical and linguistic diversity. [3] We recruit
participants primarily through [Prolific,](https://www.prolific.com/) except in
Nigeria, where we use snowball sampling due to
limited platform availability. All participants selfidentify as at least proficient in English.
Each participant completes 4 randomly assigned
tasks from our pool of 18, presented in randomized order: 2 from higher difficulty levels (0-40%
success rate) and 2 from lower difficulty levels
(60-100% success rate). The agent model remains
GPT-4o throughout all interactions. Participants
are shown task instructions (see Appendix A.5)
and asked to complete all mentioned requests by
interacting with the agent through a Streamlit chat
interface. After finishing each conversation, they
click an “End Conversation” button to proceed to
the next task. In total, the expected time to complete all 4 tasks is 35-40 minutes.
Participants provide demographic information
including education level, AI familiarity, and frequency of AI tool usage. For US participants, we
screen for White Standard American English (SAE)
speakers and Black African American Vernacular
English (AAVE) speakers based on self-reported
race and dialect, as these groups are commonly

<!-- p:35 -->
2GPT-4o (May 2024) predates _τ_ -Bench (June 2024), avoiding contamination issues present in newer models. We considered Sonnet 3.5 (also used in the original paper) but it was
retired in October 2025.
[3https://en.wikipedia.org/wiki/List_of_](https://en.wikipedia.org/wiki/List_of_countries_by_English-speaking_population)
[countries_by_English-speaking_population](https://en.wikipedia.org/wiki/List_of_countries_by_English-speaking_population)

<!-- p:36 -->
3

<!-- p:37 -->
studied in AI fairness research (Sap et al., 2019;
Groenwold et al., 2020). We also stratify US participants by age (18-34, 35-54, and 55+) to capture potential differences in technology experience
(Pew Research Center, 2025). Due to participant
availability constraints, we only recruit from the
18-34 age group for other countries. In total, we
recruit _∼_ 40 participants per age × dialect/country
group. [4]

<!-- p:38 -->
**3.4** **Evaluation Metrics**

<!-- p:39 -->
**Success Rate** To recap, a task completion in _τ_ Bench is considered successful ( _reward_ = 1) if
and only if the agent correctly executes all required
actions and its responses convey all information
specified in the instructions. We define success rate
as the percentage of tasks that are successfully completed. We apply the same automated evaluation
procedure used in _τ_ -Bench to both human and simulated user interactions. Success rate is averaged
across difficulty levels to obtain a single value.

<!-- p:40 -->
**Expected Calibration Error (ECE)** We adapt
_Expected Calibration Error (ECE)_, commonly used
for assessing confidence calibration in probabilistic
classifiers, to quantify how well simulated users
serve as proxies for human users. While traditional
ECE evaluates whether a model’s predicted probabilities match true observed outcomes, we use an
ECE-style formulation to measure whether agent
success rates with simulated users align with agent
success rates with real users across task difficulty
levels. Just as traditional ECE measures whether
predicted confidences are calibrated to observed
outcomes (Guo et al., 2017), our metric measures
calibration between agent performance distributions under simulated and real user conditions.
Let _s_ [(] _i_ [LLM][)] denote success rate with LLMsimulated users and _s_ [(] _i_ [Human][)] denote success rate
with human users at difficulty level _i_ . Let _wi_ denote
the proportion of human task completions at level
_i_, with [�] _i_ _[w][i]_ [= 1][.] [We define:]

<!-- p:41 -->
ECEHuman–LLM =

<!-- p:42 -->
_M_

<!-- p:43 -->
- (Human)

<!-- p:44 -->
_wi_ �� _si_ _−_ _s_ [(] _i_ [LLM][)] ��
_i_ =1

<!-- p:45 -->
This metric captures the weighted average absolute deviation between agent performance when interacting with simulated users vs. real users across
_M_ difficulty levels, with lower values indicating

<!-- p:46 -->
4With the exception of the AAVE 55+ group, for which we
were only able to recruit 22 participants.

<!-- p:47 -->
**User Model** **Success Rate (%)**

<!-- p:48 -->
GPT-4o 67.8 _±_ 1.2
Sonnet 3.7 67.0 _±_ 3.3
Sonnet 4.5 75.9 _±_ 3.5
Kimi-K2-Thinking 71.3 _±_ 1.9

<!-- p:49 -->
Table 1: _τ_ -Bench success rate (%) on retail tasks
( _n_ = 115) for different user models. The agent model
remains GPT-4o. The average success rates and standard deviations are shown across 3 runs.

<!-- p:50 -->
better calibration. If simulated users are perfectly
calibrated to real users, _ECE_ Human–LLM = 0.
As a reminder, we partition tasks into six difficulty levels based on agent success rates with
simulated users across five runs. We set _wi_ proportional to the number of human task completions
at level _i_ . We multiply _ECE_ Human–LLM by 100 to
report values as percentages.

<!-- p:51 -->
**4** **Results**

<!-- p:52 -->
**4.1** **Robustness**

<!-- p:53 -->
We first evaluate the robustness of user simulation
by examining how success rates vary with different user simulation models, which is largely overlooked in current evaluations. [5] We find that changing just the user LLM while keeping the agent LLM
fixed (GPT-4o) can provide different depictions of
agent performance. As shown in Table 1, GPT4o, Sonnet 3.7, and Kimi-K2-Thinking show overlapping intervals, clustering around 67-71% success rates. However, there is nearly a 9 percentage
point difference in success rates between Sonnet
3.7 and Sonnet 4.5 as the user model. [6] While Sonnet 3.7 is generally considered a stronger model
than GPT-4o, [7] using GPT-4o as the user model
yields a slightly higher success rate (67 _._ 8 vs. 67 _._ 0)
and lower standard deviation (1 _._ 2 vs. 3 _._ 3), suggesting that closer alignment between agent and
user LLMs may lead to more stable evaluation outcomes. Overall, the sensitivity of agent performance to user model choice raises concerns about
the reliability of single-model user simulations and
underscores the need for reporting results across
multiple user models to establish robustness.

<!-- p:54 -->
5For robustness, we vary the user LLM and evaluate on
all retail tasks; for validity and fairness analyses, we evaluate
with human users on a difficulty-balanced subset of tasks.
6It is difficult to disentangle increased model capability
from potential data contamination.
[7https://lmarena.ai/leaderboard/text](https://lmarena.ai/leaderboard/text)

<!-- p:55 -->
4

<!-- p:56 -->
100

<!-- p:57 -->
80

<!-- p:58 -->
60

<!-- p:59 -->
40

<!-- p:60 -->
20

<!-- p:61 -->
0

<!-- p:62 -->
0 20 40 60 80 100
Success Rate with Simulated Users (%)

<!-- p:63 -->
Figure 2: Success rate with human users vs. LLMsimulated users for United States participants, with an
_ECE_ Human–LLM of 15 _._ 1. Error bars indicate _±_ 1 SD.

<!-- p:64 -->
**4.2** **Validity**

<!-- p:65 -->
We now examine the validity of user simulation
and first consider simulated users as a proxy for
human users in the United States. Since prior work
has shown that LLMs exhibit a Western, Anglocentric bias (Tao et al., 2024; Wang et al., 2024;
Agarwal et al., 2025), LLM-simulated users might
be more representative or better calibrated to users
in the US than to users in non-Western countries.
Therefore, we assess whether simulated users are
well-calibrated to human users in the setting where
we expect the strongest alignment.

<!-- p:66 -->
We find that agents achieve a 45 _._ 2% success
rate with US participants and an _ECE_ Human–LLM
of 15 _._ 1, indicating substantial miscalibration even
in this setting. Calibration errors are not uniform across task difficulty. As shown in Figure 2, the calibration gap is most pronounced for
the 1st (0%) and 4th (60%) difficulty bins with
_ECE_ Human–LLM = 25 _._ 9 across the two bins. These
results indicate that evaluations with simulated
users underestimate agent success on the hardest
tasks (success with human users: 30 _._ 8%) while
overestimating it on moderate tasks (success with
human users: 39 _._ 0%).

<!-- p:67 -->
**4.3** **Fairness**

<!-- p:68 -->
To assess whether these findings are consistent
across different user groups, we now partition our
US results by English dialect (Standard American
English and African American Vernacular English)
and age group (18-34, 35-54, and 55+), and expand
our analysis to three non-Western countries with
high English-speaking populations (India, Kenya,
and Nigeria).

<!-- p:69 -->
**Age Group** **Success Rate (** _↑_ **)** **ECE (** _↓_ **)**
**SAE**
All 50.6 11.7
18–34 49.2 13.0
35–54 52.2 11.3
55+ 52.1 14.5
**AAVE**
All 39.4 20.3
18–34 41.0 18.9
35–54 39.9 21.6
55+ 33.4 20.5

<!-- p:70 -->
Table 2: Success Rate (%) and Expected Calibration Error ( _ECE_ Human–LLM) for Standard American English (SAE) and African American Vernacular English
(AAVE) speaking participants, split by age group.

<!-- p:71 -->
**4.3.1** **Dialect and Age (United States)**

<!-- p:72 -->
Starting with US participants, we previously saw
that agents achieve a 45 _._ 2% success rate and an
_ECE_ Human–LLM of 15 _._ 1. When further breaking
this down by dialect, we observe notable disparities in both performance and calibration, as shown
in Table 2 and Figure 3. A Generalized Estimating
Equations (GEE) model accounting for age, education, AI experience, AI usage, and task difficulty
confirms a statistically significant dialect disparity
( _β_ = 0 _._ 61, _p_ _<_ 0 _._ 001). Agents exhibit a success
rate of 50 _._ 6% with an _ECE_ Human–LLM of 11 _._ 7 for
SAE participants vs. a success rate of 39 _._ 4% with
an _ECE_ Human–LLM of 20 _._ 3 for AAVE participants.
For AAVE participants, agents perform worse (11 _._ 2
percentage point decrease in success rate) and simulated users are more poorly calibrated (8 _._ 6 percentage point increase in ECE). In practice, such
differences in performance and user simulation reliability could lead to disparities in the quality of
retail assistance and the ease of interactions.
We observe contrasting age-related patterns in
success rates across dialects. For SAE participants,
success rates increase slightly with age ( _∼_ 3 _._ 0 percentage point increase from 18-34 to 55+ group),
whereas for AAVE participants, success rates decrease with age (7 _._ 6 percentage point decrease
from 18-34 to 55+ group). Notably, dialect disparities in agent performance grow larger with age:
there is nearly a 12 percentage point decrease in
agent performance between SAE and AAVE 35-54
groups and a 19 percentage point decrease in agent
performance between SAE and AAVE 55+ groups
(age-stratified GEE dialect effects: _β_ 35 _−_ 54 = 0 _._ 67,
_p_ = 0 _._ 01; _β_ 55+ = 1 _._ 24, _p_ = 0 _._ 001). The calibra

<!-- p:73 -->
5

<!-- p:74 -->
100

<!-- p:75 -->
80

<!-- p:76 -->
60

<!-- p:77 -->
40

<!-- p:78 -->
20

<!-- p:79 -->
0

<!-- p:80 -->
100

<!-- p:81 -->
80

<!-- p:82 -->
60

<!-- p:83 -->
40

<!-- p:84 -->
20

<!-- p:85 -->
0

<!-- p:86 -->
0 20 40 60 80 100
Success Rate with Simulated Users (%)

<!-- p:87 -->
(a) SAE, 18-34

<!-- p:88 -->
0 20 40 60 80 100
Success Rate with Simulated Users (%)

<!-- p:89 -->
(d) AAVE, 18-34

<!-- p:90 -->
0 20 40 60 80 100
Success Rate with Simulated Users (%)

<!-- p:91 -->
(b) SAE, 35-54

<!-- p:92 -->
0 20 40 60 80 100
Success Rate with Simulated Users (%)

<!-- p:93 -->
(e) AAVE, 35-54

<!-- p:94 -->
0 20 40 60 80 100
Success Rate with Simulated Users (%)

<!-- p:95 -->
(c) SAE, 55+

<!-- p:96 -->
0 20 40 60 80 100
Success Rate with Simulated Users (%)

<!-- p:97 -->
(f) AAVE, 55+

<!-- p:98 -->
100

<!-- p:99 -->
80

<!-- p:100 -->
60

<!-- p:101 -->
40

<!-- p:102 -->
20

<!-- p:103 -->
0

<!-- p:104 -->
100

<!-- p:105 -->
80

<!-- p:106 -->
60

<!-- p:107 -->
40

<!-- p:108 -->
20

<!-- p:109 -->
0

<!-- p:110 -->
100

<!-- p:111 -->
80

<!-- p:112 -->
60

<!-- p:113 -->
40

<!-- p:114 -->
20

<!-- p:115 -->
0

<!-- p:116 -->
100

<!-- p:117 -->
80

<!-- p:118 -->
60

<!-- p:119 -->
40

<!-- p:120 -->
20

<!-- p:121 -->
0

<!-- p:122 -->
Figure 3: Success rate with human users vs. LLM-simulated users for SAE (top) and AAVE (bottom) participants
across different age groups (18-34, 35-54, and 55+). Note: The x-axis (success rate with simulated users) remains
the same for all groups.

<!-- p:123 -->
tion gap is particularly pronounced for the 35-54
age group (10 _._ 3 _ECE_ Human–LLM gap), where SAE
primarily exhibits miscalibration for the 1st bin,
while AAVE exhibits miscalibration across all bins
(Figures 3b and 3e).
Note that success rate and _ECE_ Human–LLM capture distinct aspects of performance. While _higher_
success rate and _lower ECE_ Human–LLM are both desirable, since higher success rates reflect stronger
agent task performance and lower _ECE_ Human–LLM
indicates that simulated users serve as reliable proxies for human users, improvements in one do not
necessarily imply improvements in the other. For
example, SAE participants aged 18–34 exhibit both
lower success rates and _ECE_ Human–LLM, whereas
SAE participants aged 55+ exhibit both higher success rates and _ECE_ Human–LLM.

<!-- p:124 -->
**4.3.2** **Countries**

<!-- p:125 -->
Due to participant availability constraints, we focus our cross-country analysis on the 18-34 age
group. We find that differences in agent performance, shown in Table 3, are present but much
less pronounced across countries (ranging from
41 _._ 0%-49 _._ 2%) than those observed by dialect and
age within the US (Table 2). In particular, Kenyan
and Nigerian participants experience similar success rates (43 _._ 5% and 43 _._ 7%). A GEE model con

<!-- p:126 -->
**Group** **Success Rate (** _↑_ **)** **ECE (** _↓_ **)**
SAE 49.2 13.0
AAVE 41.0 18.9
India 46.2 18.9
Kenya 43.5 15.6
Nigeria 43.7 17.6

<!-- p:127 -->
Table 3: Success Rate (%) and Expected Calibration
Error ( _ECE_ Human–LLM) across dialects and countries for
18–34 age group participants.

<!-- p:128 -->
firms that cross-country differences are _not_ statistically significant (all _p >_ 0 _._ 49).

<!-- p:129 -->
Simulated users are best calibrated to SAE
participants ( _ECE_ Human–LLM = 13 _._ 0) and worst
calibrated to AAVE and Indian participants
( _ECE_ Human–LLM = 18 _._ 9), suggesting simulated
users are especially poor proxies for these groups.
Across countries, we observe that simulated users
tend to exhibit strongest calibration for fairly to
moderately difficult tasks (20%-40% difficulty
bins). However, they consistently overestimate
performance for easy tasks (80%-100% difficulty
bins), shown in Figure 4. As a result, evaluations
relying on simulated users risk systematically underestimating difficulty agents face when deployed
to diverse, global user populations.

<!-- p:130 -->
6

<!-- p:131 -->
100

<!-- p:132 -->
80

<!-- p:133 -->
60

<!-- p:134 -->
40

<!-- p:135 -->
20

<!-- p:136 -->
0

<!-- p:137 -->
0 20 40 60 80 100
Success Rate with Simulated Users (%)

<!-- p:138 -->
(a) United States (SAE)

<!-- p:139 -->
0 20 40 60 80 100
Success Rate with Simulated Users (%)

<!-- p:140 -->
(b) United States (AAVE)

<!-- p:141 -->
0 20 40 60 80 100
Success Rate with Simulated Users (%)

<!-- p:142 -->
(c) India

<!-- p:143 -->
100

<!-- p:144 -->
80

<!-- p:145 -->
60

<!-- p:146 -->
40

<!-- p:147 -->
20

<!-- p:148 -->
0

<!-- p:149 -->
100

<!-- p:150 -->
80

<!-- p:151 -->
60

<!-- p:152 -->
40

<!-- p:153 -->
20

<!-- p:154 -->
0

<!-- p:155 -->
100

<!-- p:156 -->
80

<!-- p:157 -->
60

<!-- p:158 -->
40

<!-- p:159 -->
20

<!-- p:160 -->
0

<!-- p:161 -->
0 20 40 60 80 100
Success Rate with Simulated Users (%)

<!-- p:162 -->
(d) Kenya

<!-- p:163 -->
0 20 40 60 80 100
Success Rate with Simulated Users (%)

<!-- p:164 -->
(e) Nigeria

<!-- p:165 -->
100

<!-- p:166 -->
80

<!-- p:167 -->
60

<!-- p:168 -->
40

<!-- p:169 -->
20

<!-- p:170 -->
0

<!-- p:171 -->
Figure 4: Success rate with human users vs. LLM-simulated users across dialect and country groups. All participants
are in the 18–34 age group.

<!-- p:172 -->
**4.4** **Analyzing Interactions**

<!-- p:173 -->
**4.4.1** **Structure and Content**

<!-- p:174 -->
Interactions between agents and simulated users vs.
human users follow similar structures and surfacelevel forms, including # of turns, # of actions, and
# of words/turn. We observe some differences between simulated and human user interactions when
considering conversational content (Table 6). Simulated user conversations include questions in 18 _._ 8%
of user turns and 51 _._ 8% of agent turns, compared
to 9 _._ 8% and 56 _._ 3%, respectively, for human users.
Notably, Nigerian participants only ask questions
in 4 _._ 3% of turns.

<!-- p:175 -->
Differences are more pronounced when examining politeness indicators (e.g., please, thank you,
apologize). Simulated user conversations include
such indicators in 39 _._ 2% of user and 52 _._ 0% of
agent turns, compared to 19 _._ 9% and 41 _._ 1%, respectively, for human users. For both questionasking and politeness indicators, differences in behavior are more pronounced between simulated and
human users than among human users. We also
show that targeted behavioral interventions, such
as prompting simulated users to limit politeness,
can alter calibration patterns and reduce gaps for
highly miscalibrated groups (see Appendix A.6),
indicating that prompting strategies can partially
mitigate miscalibration issues.

<!-- p:176 -->
**4.4.2** **Errors**

<!-- p:177 -->
We analyze differences in (1) error types and (2)
error attribution for simulated vs. human user interactions to understand whether both groups experience the same failure modes. Error types include
argument errors, missing actions, extra actions, and
output errors (see Table 4 for definitions).

<!-- p:178 -->
Agents make argument errors (performing
the correct action with incorrect arguments) at
rates of 32 _._ 2% for simulated users compared to
23 _._ 2%–45 _._ 8% for human users, with AAVE participants experiencing the highest errors. Agents
tend to omit actions (17 _._ 8% vs. 15 _._ 8%–25 _._ 3%) or
include unnecessary ones (5 _._ 6% vs. 7 _._ 6%–13 _._ 3%)
less frequently for simulated users compared to
human users. However, output errors show the
reverse pattern: agents either omit or include incorrect outputs more often for simulated users (31 _._ 4%)
than for human users (12 _._ 2%–23 _._ 6%). These patterns suggest that agents exhibit different behavior
when interacting with simulated vs. human users;
they perform more complete and efficient action
sequences but make more frequent output errors.

<!-- p:179 -->
When comparing error attribution for simulated
vs. human user conversations (Table 5), we observe
clear differences in where task failures occur. For
simulated conversations, agents are responsible for
task failures substantially more often than for human conversations (48 _._ 9% vs. 24 _._ 5%). In contrast,

<!-- p:180 -->
7

<!-- p:181 -->
**Group** **Arg (%)** **Miss (%)** **Extra (%)** **Output (%)**
**Simulated User**

<!-- p:182 -->
- 32.2 17.8 5.6 31.4
**Human User – US, SAE**
All 25.2 18.5 9.5 16.2
18–34 27.9 15.8 7.6 18.9
35–54 24.5 18.5 10.6 17.0
55+ 23.2 21.3 10.3 12.2
**Human User – US, AAVE**
All 39.0 23.0 10.7 15.5
18–34 36.8 25.3 13.3 15.5
35–54 37.8 20.4 8.7 16.4
55+ 45.8 24.1 9.6 13.3
**Human User – Non-US, 18–34**
India 33.3 18.2 7.9 20.4
Kenya 38.5 17.2 7.8 23.6
Nigeria 33.8 22.3 10.8 21.7

<!-- p:183 -->
Table 4: Error breakdown (%) for simulated and human users, aggregated across tasks. The min and max are
highlighted per column. Error types: **argument error** (action taken matches ground truth action but with different
arguments), **missing action error** (ground truth action is missing from actions taken), **extra action error** (actions
taken go beyond ground truth actions), and **output error** (expected outputs are missing/incorrect). Each error type is
measured as a binary indicator per task (e.g., a missing action error records whether **any** required action is missing).
Note that error percentages do not sum to 100%; some tasks have no errors while others have multiple error types.

<!-- p:184 -->
**Source** **Simulated** **Human**
Agent 48.9 24.5
User 40.0 62.2
Both 2.2 11.1
Other 8.9 2.2

<!-- p:185 -->
Table 5: Error Attribution (%) for simulated vs. human
user conversations with _reward_ = 0, manually annotated by the authors ( _n_ = 45 per condition, matched on
task difficulty).

<!-- p:186 -->
users are the primary source of failure in human
conversations (62.2% vs. 40%).
These differences point to distinct failure patterns in simulated versus human interactions. The
higher user error rate in human interactions reflects
ambiguity, misunderstandings, or partial compliance that humans naturally introduce. Conversely,
the higher agent error rate in simulated conversations suggests simulated users appear to exhibit
more precise instruction following or adapt more
readily to agent responses, placing greater burden
on agents to execute correctly. In practice, this
divergence may lead to misdiagnoses of failures.
Simulation-based evaluations may overemphasize
agent execution errors, while obscuring challenges
that arise when real users engage with agents in
ways not reflected by simulated users.

<!-- p:187 -->
**5** **Discussion and Conclusion**

<!-- p:188 -->
As AI agents become integrated into everyday
tasks, ensuring equitable performance across diverse populations is essential. However, the “user”
component of agentic evaluations, central to realworld interaction, has largely been overlooked. Our
findings reveal fundamental limitations of LLMsimulated users, showing that current simulation
practices misestimate agent performance for actual
users and obscure demographic disparities, which
may result in evaluations optimizing for objectives
that diverge from real-world use.

<!-- p:189 -->
Systems optimized for simulated users may appear robust in benchmarks while failing disproportionately for real users whose communication
styles are underrepresented by simulation. For
example, the behavioral artifacts we observe in
simulated interactions—such as heightened politeness and question-asking—suggest that simulated
users reflect communication norms that may not
generalize across diverse user groups. Moving forward, agentic benchmarks should assess robustness
across multiple simulation models, validate simulated outcomes against demographically diverse
human data if possible, and transparently acknowledge the limitations of user simulation.

<!-- p:190 -->
8

<!-- p:191 -->
**Limitations**

<!-- p:192 -->
While our study provides important insights into
user simulation in agentic evaluations, it is useful
to clarify its scope and outline directions for future
work. Our evaluation is conducted entirely in English (replicating a limitation of popular agentic
benchmarks, which are limited to English), which
restricts our ability to assess how LLM-simulated
users behave in multilingual settings. Since language influences user and agent behavior, capabilities, and interaction norms, it is important to
verify the extent to which our findings hold for
non-English contexts. In addition, our age-based
analyses are limited to users in the United States
due to recruitment constraints, leaving open the
question of how performance and calibration disparities vary with age across other countries and
cultural contexts.
We also evaluate agents in a single domain, focusing on retail customer service scenarios from
_τ_ -Bench. While these tasks are designed to capture multi-turn, task-oriented interactions with tool
use, agent performance patterns and the quality of
user simulation may differ in other domains such
as healthcare, where interaction structure and task
complexity vary. In such domains with longer-form
interactions, individual style and cultural differences may be more apparent, potentially amplifying the effects we observe. Nevertheless, it would
be important to empirically validate this expectation.
Finally, we focus on a single, fixed agent (GPT4o). Holding the agent constant enables us to isolate the effects of user simulation on evaluation
outcomes. However, we do not examine how calibration gaps or performance disparities vary across
different agents, which is important for developing
a more complete understanding of the robustness,
validity, and fairness of user simulation. We discuss
these points further in Appendix A.1.

<!-- p:193 -->
**Ethics Statement**

<!-- p:194 -->
All participants received standardized compensation that was not adjusted by country, ensuring
consistent and fair payment regardless of geographic location. Participants were provided with
an overview of the study procedures upfront and
could withdraw from the study at any point without
penalty. Participants provided informed consent
by reading the study instructions and choosing to
participate and complete the study. The study is

<!-- p:195 -->
classified as minimal risk, since it involves interaction with AI agents in simulated retail customer
service scenarios and does not involve the collection of sensitive personal information.
Beyond the user study itself, our work has
broader societal implications. Our results demonstrate that LLM-simulated users may not serve as
reliable proxies for human users and can exhibit
demographic biases. If simulated users are adopted
as a standard practice for agent evaluation despite
these limitations, there is a risk that AI systems
could be deployed in ways that systematically underserve certain demographic groups. We hope
this work encourages the research community to reflect on current evaluation practices and to develop
agentic evaluation approaches that better represent
diverse user populations.

<!-- p:196 -->
**Acnkowledgements**

<!-- p:197 -->
We thank Ava Batchkala, Boyu Fan, Nithya Govindarajan, Keith Hall, Mads Jenkins, Kelly Marchisio,
Harry Moynehan, Kailash Saravanakumar, Alice
Schoenauer Sebag, Priyanka Sen, Jimin Sun, and
Pat Verga for piloting our user study and providing
feedback. We also thank the members of UCI NLP
for helpful discussions and comments. This work
was conducted primarily during Preethi’s internship at Cohere, and was supported in part by the
Hasso Plattner Institute (HPI) and NSF CAREER
award number IIS-2046873.

<!-- p:198 -->
**References**

<!-- p:199 -->
Dhruv Agarwal, Mor Naaman, and Aditya Vashistha.
2025. Ai suggestions [homogenize](https://doi.org/10.1145/3706598.3713564) writing toward
[western styles and diminish cultural nuances.](https://doi.org/10.1145/3706598.3713564) CHI
’25, New York, NY, USA. Association for Computing
Machinery.

<!-- p:200 -->
Victor Barres, Honghua Dong, Soham Ray, Xujie Si,
and Karthik Narasimhan. 2025. _τ_ [2] [-bench:](https://arxiv.org/abs/2506.07982) Evaluat[ing conversational agents in a dual-control environ-](https://arxiv.org/abs/2506.07982)
[ment.](https://arxiv.org/abs/2506.07982) _Preprint_, arXiv:2506.07982.

<!-- p:201 -->
Elisa Bassignana, Amanda Cercas Curry, and Dirk Hovy.
2025. The AI gap: [How socioeconomic status affects](https://doi.org/10.18653/v1/2025.acl-long.914)
language [technology](https://doi.org/10.18653/v1/2025.acl-long.914) interactions. In _Proceedings_
_of_ _the_ _63rd_ _Annual_ _Meeting_ _of_ _the_ _Association_ _for_
_Computational Linguistics (Volume 1:_ _Long Papers)_,
pages 18647–18664, Vienna, Austria. Association
for Computational Linguistics.

<!-- p:202 -->
Samuel Cahyawijaya, Delong Chen, Yejin Bang, Leila
Khalatbari, Bryan Wilie, Ziwei Ji, Etsuko Ishii, and
Pascale Fung. 2025. [High-dimension human value](https://doi.org/10.18653/v1/2025.naacl-long.274)
representation in [large](https://doi.org/10.18653/v1/2025.naacl-long.274) language models. In _Pro-_
_ceedings_ _of_ _the_ _2025_ _Conference_ _of_ _the_ _Nations_ _of_

<!-- p:203 -->
9

<!-- p:204 -->
_the_ _Americas_ _Chapter_ _of_ _the_ _Association_ _for_ _Com-_
_putational Linguistics:_ _Human Language Technolo-_
_gies_ _(Volume_ _1:_ _Long_ _Papers)_, pages 5303–5330,
Albuquerque, New Mexico. Association for Computational Linguistics.

<!-- p:205 -->
Serina Chang, Ashton Anderson, and Jake M. Hofman. 2025. ChatBench: From static benchmarks
[to human-AI evaluation.](https://doi.org/10.18653/v1/2025.acl-long.1262) In _Proceedings of the 63rd_
_Annual Meeting of the Association for Computational_
_Linguistics (Volume 1:_ _Long Papers)_, pages 26009–
26038, Vienna, Austria. Association for Computational Linguistics.

<!-- p:206 -->
CNBC. 2025. [Ai travel agents planning future trip far](https://www.cnbc.com/2025/05/16/ai-travel-agents-planning-future-trip-far-beyond-assistant-status.html)
[beyond assistant status.](https://www.cnbc.com/2025/05/16/ai-travel-agents-planning-future-trip-far-beyond-assistant-status.html)

<!-- p:207 -->
Kaustubh Deshpande, Ved Sirdeshmukh, Johannes Baptist Mols, Lifeng Jin, Ed-Yeremai HernandezCardona, Dean Lee, Jeremy Kritz, Willow E. Primack, Summer Yue, and Chen Xing. 2025. [Multi-](https://doi.org/10.18653/v1/2025.findings-acl.958)
Challenge: [A realistic multi-turn conversation eval-](https://doi.org/10.18653/v1/2025.findings-acl.958)
[uation benchmark challenging to frontier LLMs.](https://doi.org/10.18653/v1/2025.findings-acl.958) In
_Findings of the Association for Computational Lin-_
_guistics:_ _ACL_ _2025_, pages 18632–18702, Vienna,
Austria. Association for Computational Linguistics.

<!-- p:208 -->
Yao Dou, Michel Galley, Baolin Peng, Chris Kedzie,
Weixin Cai, Alan Ritter, Chris Quirk, Wei Xu, and
Jianfeng Gao. 2025. [SimulatorArena:](https://doi.org/10.18653/v1/2025.emnlp-main.1786) Are user simu[lators reliable proxies for multi-turn evaluation of AI](https://doi.org/10.18653/v1/2025.emnlp-main.1786)
[assistants?](https://doi.org/10.18653/v1/2025.emnlp-main.1786) In _Proceedings of the 2025 Conference_
_on Empirical Methods in Natural Language Process-_
_ing_, pages 35200–35278, Suzhou, China. Association
for Computational Linguistics.

<!-- p:209 -->
Esin Durmus, Karina Nguyen, Thomas Liao, Nicholas
Schiefer, Amanda Askell, Anton Bakhtin, Carol
Chen, Zac Hatfield-Dodds, Danny Hernandez,
Nicholas Joseph, Liane Lovitt, Sam McCandlish,
Orowa Sikder, Alex Tamkin, Janel Thamkul, Jared
Kaplan, Jack Clark, and Deep Ganguli. 2024. [To-](https://openreview.net/forum?id=zl16jLb91v)
wards measuring the [representation](https://openreview.net/forum?id=zl16jLb91v) of subjective
[global opinions in language models.](https://openreview.net/forum?id=zl16jLb91v) In _First Confer-_
_ence on Language Modeling_ .

<!-- p:210 -->
Sophie Groenwold, Lily Ou, Aesha Parekh, Samhita
Honnavalli, Sharon Levy, Diba Mirza, and
William Yang Wang. 2020. [Investigating](https://doi.org/10.18653/v1/2020.emnlp-main.473) African[American Vernacular English in transformer-based](https://doi.org/10.18653/v1/2020.emnlp-main.473)
text [generation.](https://doi.org/10.18653/v1/2020.emnlp-main.473) In _Proceedings_ _of_ _the_ _2020_ _Con-_
_ference on Empirical Methods in Natural Language_
_Processing (EMNLP)_, pages 5877–5883, Online. Association for Computational Linguistics.

<!-- p:211 -->
Chuan Guo, Geoff Pleiss, Yu Sun, and Kilian Q. Weinberger. 2017. [On calibration of modern neural net-](https://proceedings.mlr.press/v70/guo17a/guo17a.pdf)
[works.](https://proceedings.mlr.press/v70/guo17a/guo17a.pdf) In _Proceedings of the 34th International Con-_
_ference on Machine Learning - Volume 70_, ICML’17,
page 1321–1330. JMLR.org.

<!-- p:212 -->
Luna Luan Haoyue and Hichang Cho. 2024. [Factors](https://doi.org/10.1007/s10209-023-01087-7)
influencing intention to [engage](https://doi.org/10.1007/s10209-023-01087-7) in human–chatbot
interaction: [examining user perceptions and context](https://doi.org/10.1007/s10209-023-01087-7)
[culture orientation.](https://doi.org/10.1007/s10209-023-01087-7) 24(1):607–620.

<!-- p:213 -->
Muyu He, Anand Kumar, Tsach Mackey, Meghana Rajeev, James Zou, and Nazneen Rajani. 2025. [Impa-](https://arxiv.org/abs/2510.04491)
tient users confuse ai [agents:](https://arxiv.org/abs/2510.04491) High-fidelity simulations of human [traits](https://arxiv.org/abs/2510.04491) for testing agents. _Preprint_,
arXiv:2510.04491.

<!-- p:214 -->
Jonathan Ivey, Shivani Kumar, Jiayu Liu, Hua
Shen, Sushrita Rakshit, Rohan Raju, Haotian
Zhang, Aparna Ananthasubramaniam, Junghwan
Kim, Bowen Yi, Dustin Wright, Abraham Israeli,
Anders Giovanni Møller, Lechen Zhang, and David
Jurgens. 2024. Real or robotic? [assessing whether](https://arxiv.org/abs/2409.08330)
[llms accurately simulate qualities of human responses](https://arxiv.org/abs/2409.08330)
[in dialogue.](https://arxiv.org/abs/2409.08330) _Preprint_, arXiv:2409.08330.

<!-- p:215 -->
Nayeon Lee, Yejin Bang, Holy Lovenia, Samuel
Cahyawijaya, Wenliang Dai, and Pascale Fung. 2023.
Survey of social bias in vision-language models.
_Preprint_, arXiv:2309.14381.

<!-- p:216 -->
Nayeon Lee, Chani Jung, Junho Myung, Jiho Jin, Jose
Camacho-Collados, Juho Kim, and Alice Oh. 2024.
[Exploring cross-cultural differences in English hate](https://doi.org/10.18653/v1/2024.naacl-long.236)
speech annotations: [From](https://doi.org/10.18653/v1/2024.naacl-long.236) dataset construction to
[analysis.](https://doi.org/10.18653/v1/2024.naacl-long.236) In _Proceedings of the 2024 Conference of_
_the North American Chapter of the Association for_
_Computational Linguistics:_ _Human Language Tech-_
_nologies (Volume 1:_ _Long Papers)_, pages 4205–4224,
Mexico City, Mexico. Association for Computational
Linguistics.

<!-- p:217 -->
Zihan Liu, Han Li, Anfan Chen, Renwen Zhang, and
Yi-Chieh Lee. 2024. [Understanding public percep-](https://doi.org/10.1145/3613904.3642840)
tions of ai [conversational](https://doi.org/10.1145/3613904.3642840) agents: A cross-cultural
[analysis.](https://doi.org/10.1145/3613904.3642840) In _Proceedings_ _of_ _the_ _2024_ _CHI_ _Confer-_
_ence on Human Factors in Computing Systems_, CHI
’24, New York, NY, USA. Association for Computing
Machinery.

<!-- p:218 -->
Yuxuan Lu, Jing Huang, Yan Han, Bingsheng Yao,
Sisong Bei, Jiri Gesi, Yaochen Xie, Zheshen, Wang,
Qi He, and Dakuo Wang. 2025. Can [llm](https://arxiv.org/abs/2503.20749) agents
simulate multi-turn [human](https://arxiv.org/abs/2503.20749) behavior? evidence
[from real online customer behavior data.](https://arxiv.org/abs/2503.20749) _Preprint_,
arXiv:2503.20749.

<!-- p:219 -->
Shuhaib Mehri, Xiaocheng Yang, Takyoung Kim,
Gokhan Tur, Shikib Mehri, and Dilek Hakkani-Tür.
2025. [Goal alignment in llm-based user simulators](https://arxiv.org/abs/2507.20152)
[for conversational ai.](https://arxiv.org/abs/2507.20152) _Preprint_, arXiv:2507.20152.

<!-- p:220 -->
Siddhesh Pawar, Junyeong Park, Jiho Jin, Arnav
Arora, Junho Myung, Srishti Yadav, Faiz Ghifari
Haznitrama, Inhwa Song, Alice Oh, and Isabelle Augenstein. 2025. [Survey of cultural awareness in lan-](https://doi.org/10.1162/COLI.a.14)
guage models: [Text](https://doi.org/10.1162/COLI.a.14) and beyond. _Computational_
_Linguistics_, 51(3):907–1004.

<!-- p:221 -->
Pew Research Center. 2025. Ai in americans’
lives: Awareness, experiences and attitudes.
[https://www.pewresearch.org/science/2025/09/17/ai-](https://www.pewresearch.org/science/2025/09/17/ai-in-americans-lives-awareness-experiences-and-attitudes/)
[in-americans-lives-awareness-experiences-and-](https://www.pewresearch.org/science/2025/09/17/ai-in-americans-lives-awareness-experiences-and-attitudes/)
[attitudes/.](https://www.pewresearch.org/science/2025/09/17/ai-in-americans-lives-awareness-experiences-and-attitudes/) Accessed: 2025-01-04.

<!-- p:222 -->
Vinodkumar Prabhakaran, Christopher Homan, Lora
Aroyo, Aida Mostafazadeh Davani, Alicia Parrish,

<!-- p:223 -->
10

<!-- p:224 -->
Alex Taylor, Mark Diaz, Ding Wang, and Gregory
Serapio-García. 2024. [GRASP: A disagreement anal-](https://doi.org/10.18653/v1/2024.naacl-long.190)
[ysis framework to assess group associations in per-](https://doi.org/10.18653/v1/2024.naacl-long.190)
[spectives.](https://doi.org/10.18653/v1/2024.naacl-long.190) In _Proceedings of the 2024 Conference of_
_the North American Chapter of the Association for_
_Computational Linguistics:_ _Human Language Tech-_
_nologies (Volume 1:_ _Long Papers)_, pages 3473–3492,
Mexico City, Mexico. Association for Computational
Linguistics.

<!-- p:225 -->
Haoyi Qiu, Alexander Fabbri, Divyansh Agarwal, KungHsiang Huang, Sarah Tan, Nanyun Peng, and ChienSheng Wu. 2025. Evaluating [cultural](https://doi.org/10.18653/v1/2025.findings-naacl.222) and social
[awareness of LLM web agents.](https://doi.org/10.18653/v1/2025.findings-naacl.222) In _Findings of the_
_Association for Computational Linguistics:_ _NAACL_
_2025_, pages 3978–4005, Albuquerque, New Mexico.
Association for Computational Linguistics.

<!-- p:226 -->
Olawale Salaudeen, Anka Reuel, Ahmed Ahmed,
Suhana Bedi, Zachary Robertson, Sudharsan Sundar, Ben Domingue, Angelina Wang, and Sanmi
Koyejo. 2025. [Measurement to meaning:](https://arxiv.org/abs/2505.10573) A validitycentered [framework](https://arxiv.org/abs/2505.10573) for ai evaluation. _Preprint_,
arXiv:2505.10573.

<!-- p:227 -->
Shibani Santurkar, Esin Durmus, Faisal Ladhak, Cinoo
Lee, Percy Liang, and Tatsunori Hashimoto. 2023.
Whose opinions do [language](https://proceedings.mlr.press/v202/santurkar23a/santurkar23a.pdf) models reflect? In
_Proceedings of the 40th International Conference on_
_Machine Learning_, ICML’23. JMLR.org.

<!-- p:228 -->
Sebastin Santy, Jenny Liang, Ronan Le Bras, Katharina
Reinecke, and Maarten Sap. 2023. [NLPositionality:](https://doi.org/10.18653/v1/2023.acl-long.505)
[Characterizing design biases of datasets and models.](https://doi.org/10.18653/v1/2023.acl-long.505)
In _Proceedings_ _of_ _the_ _61st_ _Annual_ _Meeting_ _of_ _the_
_Association for Computational Linguistics (Volume_
_1:_ _Long Papers)_, pages 9080–9102, Toronto, Canada.
Association for Computational Linguistics.

<!-- p:229 -->
Maarten Sap, Dallas Card, Saadia Gabriel, Yejin Choi,
and Noah A. Smith. 2019. The risk [of](https://doi.org/10.18653/v1/P19-1163) racial bias
[in hate speech detection.](https://doi.org/10.18653/v1/P19-1163) In _Proceedings of the 57th_
_Annual Meeting of the Association for Computational_
_Linguistics_, pages 1668–1678, Florence, Italy. Association for Computational Linguistics.

<!-- p:230 -->
Maarten Sap, Swabha Swayamdipta, Laura Vianna,
Xuhui Zhou, Yejin Choi, and Noah A. Smith. 2022.
Annotators with [attitudes:](https://doi.org/10.18653/v1/2022.naacl-main.431) How annotator beliefs
[and identities bias toxic language detection.](https://doi.org/10.18653/v1/2022.naacl-main.431) In _Pro-_
_ceedings of the 2022 Conference of the North Amer-_
_ican Chapter of the Association for Computational_
_Linguistics:_ _Human Language Technologies_, pages
5884–5906, Seattle, United States. Association for
Computational Linguistics.

<!-- p:231 -->
Yijia Shao, Vinay Samuel, Yucheng Jiang, John Yang,
and Diyi Yang. 2025. [Collaborative gym:](https://arxiv.org/abs/2412.15701) A frame[work for enabling and evaluating human-agent col-](https://arxiv.org/abs/2412.15701)
[laboration.](https://arxiv.org/abs/2412.15701) _Preprint_, arXiv:2412.15701.

<!-- p:232 -->
Huaman Sun, Jiaxin Pei, Minje Choi, and David Jurgens. 2025. [Sociodemographic](https://doi.org/10.18653/v1/2025.naacl-short.71) prompting is not
[yet an effective approach for simulating subjective](https://doi.org/10.18653/v1/2025.naacl-short.71)
[judgments with LLMs.](https://doi.org/10.18653/v1/2025.naacl-short.71) In _Proceedings of the 2025_

<!-- p:233 -->
_Conference_ _of_ _the_ _Nations_ _of_ _the_ _Americas_ _Chap-_
_ter of the Association for Computational Linguistics:_
_Human Language Technologies (Volume 2:_ _Short Pa-_
_pers)_, pages 845–854, Albuquerque, New Mexico.
Association for Computational Linguistics.

<!-- p:234 -->
Yan Tao, Olga Viberg, Ryan S Baker, and René F Kizilcec. 2024. Cultural bias and [cultural](https://doi.org/10.1093/pnasnexus/pgae346) alignment of
[large language models.](https://doi.org/10.1093/pnasnexus/pgae346) _PNAS Nexus_, 3(9).

<!-- p:235 -->
Kimberly Truong, Riccardo Fogliato, Hoda Heidari, and
Steven Wu. 2025. [Persona-augmented benchmark-](https://doi.org/10.18653/v1/2025.emnlp-main.1155)
ing: [Evaluating LLMs across diverse writing styles.](https://doi.org/10.18653/v1/2025.emnlp-main.1155)
In _Proceedings_ _of_ _the_ _2025_ _Conference_ _on_ _Empiri-_
_cal Methods in Natural Language Processing_, pages
22687–22720, Suzhou, China. Association for Computational Linguistics.

<!-- p:236 -->
Yu-Min Tseng, Yu-Chao Huang, Teng-Yun Hsiao, WeiLin Chen, Chao-Wei Huang, Yu Meng, and YunNung Chen. 2024. [Two tales of persona in LLMs:](https://doi.org/10.18653/v1/2024.findings-emnlp.969) A
[survey of role-playing and personalization.](https://doi.org/10.18653/v1/2024.findings-emnlp.969) In _Find-_
_ings of the Association for Computational Linguistics:_
_EMNLP 2024_, pages 16612–16631, Miami, Florida,
USA. Association for Computational Linguistics.

<!-- p:237 -->
Haoxin Wang, Xianhan Peng, Huang Cheng, Yizhe
Huang, Ming Gong, Chenghan Yang, Yang Liu, and
Jiang Lin. 2025a. ECom-bench: [Can](https://doi.org/10.18653/v1/2025.emnlp-industry.19) LLM agent
[resolve real-world E-commerce customer support is-](https://doi.org/10.18653/v1/2025.emnlp-industry.19)
[sues?](https://doi.org/10.18653/v1/2025.emnlp-industry.19) In _Proceedings_ _of_ _the_ _2025_ _Conference_ _on_
_Empirical_ _Methods_ _in_ _Natural_ _Language_ _Process-_
_ing:_ _Industry Track_, pages 276–284, Suzhou (China).
Association for Computational Linguistics.

<!-- p:238 -->
Wenxuan Wang, Wenxiang Jiao, Jingyuan Huang, Ruyi
Dai, Jen-tse Huang, Zhaopeng Tu, and Michael Lyu.
2024. [Not all countries celebrate thanksgiving:](https://doi.org/10.18653/v1/2024.acl-long.345) On
[the cultural dominance in large language models.](https://doi.org/10.18653/v1/2024.acl-long.345) In
_Proceedings of the 62nd Annual Meeting of the As-_
_sociation for Computational Linguistics (Volume 1:_
_Long Papers)_, pages 6349–6384, Bangkok, Thailand.
Association for Computational Linguistics.

<!-- p:239 -->
Zhefan Wang, Ning Geng, Zhiqiang Guo, Weizhi Ma,
and Min Zhang. 2025b. Human vs. [agent](https://doi.org/10.1145/3767695.3769490) in task[oriented conversations.](https://doi.org/10.1145/3767695.3769490) In _Proceedings of the 2025_
_Annual International ACM SIGIR Conference on Re-_
_search_ _and_ _Development_ _in_ _Information_ _Retrieval_
_in_ _the_ _Asia_ _Pacific_ _Region_, SIGIR-AP 2025, page
133–142, New York, NY, USA. Association for Computing Machinery.

<!-- p:240 -->
Jian Xie, Kai Zhang, Jiangjie Chen, Tinghui Zhu, Renze
Lou, Yuandong Tian, Yanghua Xiao, and Yu Su. 2024.
Travelplanner: [a benchmark for real-world planning](https://proceedings.mlr.press/v235/xie24j.html)
[with language agents.](https://proceedings.mlr.press/v235/xie24j.html) ICML’24. JMLR.org.

<!-- p:241 -->
Jane Xing, Tianyi Niu, and Shashank Srivastava. 2025.

<!-- p:242 -->
Chameleon LLMs: [User personas influence chatbot](https://doi.org/10.18653/v1/2025.emnlp-main.875)
[personality shifts.](https://doi.org/10.18653/v1/2025.emnlp-main.875) In _Proceedings of the 2025 Con-_
_ference on Empirical Methods in Natural Language_
_Processing_, pages 17314–17332, Suzhou, China. Association for Computational Linguistics.

<!-- p:243 -->
11

<!-- p:244 -->
Frank F. Xu, Yufan Song, Boxuan Li, Yuxuan Tang, Kritanjali Jain, Mengxue Bao, Zora Zhiruo Wang, Xuhui
Zhou, Zhitong Guo, Murong Cao, Mingyang Yang,
Hao Yang Lu, Amaad Martin, Zhe Su, Leander Melroy Maben, Raj Mehta, Wayne Chi, Lawrence Keunho Jang, Yiqing Xie, and 2 others. 2025. [Theagent-](https://openreview.net/forum?id=LZnKNApvhG)
company: [Benchmarking LLM agents on consequen-](https://openreview.net/forum?id=LZnKNApvhG)
[tial real world tasks.](https://openreview.net/forum?id=LZnKNApvhG) In _The Thirty-ninth Annual Con-_
_ference on Neural Information Processing Systems_
_Datasets and Benchmarks Track_ .

<!-- p:245 -->
Shunyu Yao, Noah Shinn, Pedram Razavi, and Karthik
Narasimhan. 2025. _τ_ -bench: [A benchmark for](https://proceedings.iclr.cc/paper_files/paper/2025/file/1b126cc38b8638e07bef37e7b2bb72bf-Paper-Conference.pdf) ToolAgent-User interaction in real-world domains. In
_International Conference on Representation Learn-_
_ing_, volume 2025, pages 9965–10017.

<!-- p:246 -->
Se-eun Yoon, Zhankui He, Jessica Echterhoff, and Julian McAuley. 2024. [Evaluating large language mod-](https://doi.org/10.18653/v1/2024.naacl-long.83)
[els as generative user simulators for conversational](https://doi.org/10.18653/v1/2024.naacl-long.83)
[recommendation.](https://doi.org/10.18653/v1/2024.naacl-long.83) In _Proceedings of the 2024 Con-_
_ference of the North American Chapter of the Asso-_
_ciation for Computational Linguistics:_ _Human Lan-_
_guage Technologies (Volume 1:_ _Long Papers)_, pages
1490–1504, Mexico City, Mexico. Association for
Computational Linguistics.

<!-- p:247 -->
Shuyan Zhou, Frank F. Xu, Hao Zhu, Xuhui Zhou,
Robert Lo, Abishek Sridhar, Xianyi Cheng, Tianyue
Ou, Yonatan Bisk, Daniel Fried, Uri Alon, and Graham Neubig. 2024. Webarena: [A realistic web en-](https://openreview.net/forum?id=oKn9c6ytLx)
[vironment for building autonomous agents.](https://openreview.net/forum?id=oKn9c6ytLx) In _The_
_Twelfth International Conference on Learning Repre-_
_sentations_ .

<!-- p:248 -->
Yuxuan Zhu, Tengjun Jin, Yada Pruksachatkun, Andy K
Zhang, Shu Liu, Sasha Cui, Sayash Kapoor, Shayne
Longpre, Kevin Meng, Rebecca Weiss, Fazl Barez,
Rahul Gupta, Jwala Dhamala, Jacob Merizian, Mario
Giulianelli, Harry Coppock, Cozmin Ududec, Antony
Kellermann, Jasjeet S Sekhon, and 7 others. 2025. [Es-](https://openreview.net/forum?id=E58HNCqoaA)
[tablishing best practices in building rigorous agentic](https://openreview.net/forum?id=E58HNCqoaA)
[benchmarks.](https://openreview.net/forum?id=E58HNCqoaA) In _The Thirty-ninth Annual Conference_
_on Neural Information Processing Systems Datasets_
_and Benchmarks Track_ .

<!-- p:249 -->
**A** **Appendix**

<!-- p:250 -->
**A.1** **Design Choices**

<!-- p:251 -->
**Single Agent** We use GPT-4o as the agent model
throughout all experiments to isolate the effect of
user variation while holding agent capability constant. This design choice allows us to attribute
observed differences in performance to user simulation rather than differences in agent performance.
While agent model choice may influence absolute
success rates, the core questions investigated in
this paper (robustness, validity, and fairness of user
simulation) are agent-agnostic.
We acknowledge that we cannot assess whether
these issues vary across agents of different capabilities. Future work should examine whether weaker

<!-- p:252 -->
or stronger agents exhibit different calibration patterns when interacting with simulated vs. human
users.

<!-- p:253 -->
**Single** **Benchmark** Our analysis focuses on _τ_ Bench as a case study, but we expect similar evaluation concerns to arise across agentic benchmarks
that rely on simulated users. The core challenges
we identify (sensitivity to user simulation model,
miscalibration across difficulty levels, and demographic biases) are likely to apply to AI agents
designed to perform multi-turn, tool-using task
completion. However, benchmarks with different task structures (e.g., web navigation vs. conversational assistance), evaluation metrics (e.g.,
trajectory-based vs. outcome-based), or user simulation prompting strategies may exhibit varying
degrees of these issues. A comprehensive investigation across multiple benchmarks remains an
important direction for future work.

<!-- p:254 -->
**A.2** **Dialect Screening**

<!-- p:255 -->
For US participants, we used Prolific’s participant filters to recruit White and Black participants. As part of prescreening (in addition to questions about education, AI experience, and AI usage), we asked participants to self-identify their
primary English dialect. Specifically, we asked:
“Which of the following best describes your everyday English usage?” with the following response
options: (1) Mostly Standard American English
(SAE), (2) Mostly African American Vernacular
English (AAVE), (3) A mixture of SAE and AAVE,
and (4) Not sure. We retained participants who
identified as White/SAE or Black/AAVE for our
analysis.

<!-- p:256 -->
**A.3** **Statistical Analysis**

<!-- p:257 -->
We use Generalized Estimating Equations (GEE)
to assess the statistical significance of demographic
differences in task success while accounting for the
repeated-measures structure of our data, as each
participant completes four tasks. We model binary
success outcomes using a binomial family and cluster observations by participant ID.
We fit two types of models: (1) an overall model
including all participants with covariates for age
(for United States only), dialect/country, education,
AI exposure, AI usage, and task difficulty (operationalized via model-based success-rate bins described in Section 3.2) and (2) age-stratified models fit separately for each age group (18–34, 35–

<!-- p:258 -->
12

<!-- p:259 -->
**Group** **Turns** **Actions** **W/T (U)** **W/T (A)** **Q (U)** **Q (A)** **P (U)** **P (A)**
**Simulated User**

<!-- p:260 -->
- 16.2 7.9 13.4 55.0 18.8 51.8 39.2 52.0
**Human User – US, SAE**
All 15.0 7.4 12.6 53.0 11.6 56.6 19.1 41.1
18–34 15.8 7.6 11.4 55.4 14.5 58.1 15.6 41.1
35–54 14.9 7.3 11.6 51.5 9.8 55.3 19.7 43.6
55+ 14.3 7.3 14.8 51.9 10.3 56.2 22.1 38.7
**Human User – US, AAVE**
All 14.9 7.4 12.4 52.8 10.0 56.4 19.7 42.5
18–34 15.5 7.6 11.9 52.6 12.8 56.8 17.4 44.9
35–54 14.8 7.3 12.1 53.4 8.9 57.2 19.9 42.1
55+ 15.3 7.0 13.9 51.9 9.1 53.9 24.0 38.3
**Human User – Non-US, 18–34**
India 16.3 7.4 11.5 53.1 9.9 57.7 20.1 40.8
Kenya 14.4 8.0 13.7 54.6 8.9 54.7 21.4 39.1
Nigeria 14.4 7.5 11.2 55.6 4.3 56.8 18.7 41.4

<!-- p:261 -->
Table 6: Conversational statistics (means) for simulated users and human users (split by demographic group).
Statistics include: **Turns** - number of turns in the interaction, **Actions** - total number of actions performed by the
agent (including read and write actions), **W/T (U/A)** - words per turn, for the user/agent, **Q (U/A)** - percent of turns
with a question, for the user/agent, **P (U/A)** - percent of turns with politeness indicators (e.g., please, thank you,
apologize, etc.), for the user/agent.

<!-- p:262 -->
**Age Group** ∆ _ECE_
**US, SAE**
All 2.4
18–34 -5.0
35–54 3.3
55+ 5.5
**US, AAVE**
All -4.9
18–34 -2.6
35–54 -6.0
55+ -0.3
**Non-US, 18–34**
India -6.2
Kenya -4.2
Nigeria 1.0

<!-- p:263 -->
Table 7: Differences between _ECE_ Human–LLM for
reduced-politeness user simulation across demographic
groups vs. standard user simulation. Negative values
indicate better calibration after behavioral intervention.
Human user study results are held fixed, while task difficulty bins are recomputed based on updated simulated
user results, resulting in changes to _ECE_ Human–LLM.

<!-- p:264 -->
54, 55+) to examine how dialect effects vary by
age. Coefficients represent log-odds of task success; we report estimated coefficients and associated p-values.

<!-- p:265 -->
**A.4** _τ_ **-Bench Adaptation**

<!-- p:266 -->
We modify task instructions to ensure that neither
simulated nor human users are influenced by identity and behavioral cues in the instructions when
completing tasks. First, we remove user names
(e.g., Yusuf Rossi) from instructions and replace
them with anonymized user IDs following the format [a-z][0-9][0-9] (e.g., o32). Second, we remove
behavioral cues (e.g., "You are detail-oriented and
want to make sure everything is addressed in one
go") to avoid biasing user behavior (Tseng et al.,
2024; Xing et al., 2025). These modifications preserve all task objectives and requirements.

<!-- p:267 -->
**Example of Original Task Instructions** _You are_
_Yusuf_ _Rossi_ _in_ _19122._ _You_ _received_ _your_ _order_
_#W2378156 and wish to exchange the mechanical_
_keyboard for a similar one but with clicky switches_
_and the smart thermostat for one compatible with_
_Google Home instead of Apple HomeKit._ _If there is_
_no keyboard that is clicky, RGB backlight, full size,_
_you’d rather only exchange the thermostat._ _You are_
_detail-oriented and want to make sure everything_
_is addressed in one go._

<!-- p:268 -->
**Example** **of** **Adapted** **Task** **Instructions** _You_
_are User b63 in 19122._ _You received your order_
_#W2378156 and wish to exchange the mechanical_
_keyboard for a similar one but with clicky switches_

<!-- p:269 -->
13

<!-- p:270 -->
_and the smart thermostat for one compatible with_
_Google Home instead of Apple HomeKit._ _If there_
_is no keyboard that is clicky,_ _RGB backlight,_ _full_
_size, you would rather exchange only the thermo-_
_stat._ _You want to make sure everything is addressed_
_in one go._ _To start the conversation, say ’Hello, my_
_email is user.b63@example.com.’_

<!-- p:271 -->
**A.5** **User Study Interface and Instructions**

<!-- p:272 -->
Users interact with a Streamlit app (Figure 5) to
converse with the agent and complete tasks. We
provide participants with the following general instructions, which apply to all tasks in addition to
the task-specific instructions shown in Table 8.

<!-- p:273 -->
**Instructions:** Please respond as the user described in the task instructions. You want to complete all the requests mentioned in the instructions.
The agent is there to assist you with completing the
task. Do not make up information beyond what the
instructions provide. You can tell the agent you are
unsure and ask them to look up information based
on your profile or orders. Beyond this, please behave naturally and converse as you normally would.
Use the ‘End Conversation’ button in the left sidebar to finish your conversation. To begin the conversation, authenticate yourself by providing the
user email provided in the instructions.

<!-- p:274 -->
Note that all task instructions are free of user persona information and use generic user IDs to avoid
biasing interactions.

<!-- p:275 -->
**A.6** **Behaviorally Targeted User Simulation**

<!-- p:276 -->
We previously identified heightened politeness as
a behavioral artifact in simulated user interactions.
Motivated by this observation, we examine whether
explicitly constraining this behavior affects evaluation outcomes. To test this, we introduce a minimal
intervention to the user simulation prompt that limits the use of politeness indicators while preserving
task objectives: “You may include politeness indicators (e.g., please, thank you, sorry) occasionally,
but use them sparingly. Limit their use to at most
one or two times across the entire conversation.”
We re-run user simulation on the 18-task subset using GPT-4o as both the agent and user LLMs, and
re-bucket tasks based on the updated performance
distribution. We find that 11 of 18 tasks shift difficulty bins, indicating that task difficulty estimates
are sensitive to behavioral prompting, and overall
success decreases from 50.0% to 46.7%.

<!-- p:277 -->
Comparing _ECE_ Human–LLM with and without behavioral prompting, we observe improved
calibration for AAVE, Indian, and Kenyan
participants—groups that previously exhibited the
largest calibration errors—while calibration worsens for SAE and Nigerian participants (Table 7).
These results highlight the sensitivity of user simulation to prompt-level choices and suggest that
targeted behavioral interventions can alter calibration patterns.

<!-- p:278 -->
**A.7** **Country-Based User Simulation**

<!-- p:279 -->
In addition to the behavioral intervention, we also
perform a demographic prompting intervention by
providing a country-specific first name and location indicator (e.g., “Your name is Ramesh and
you are from Mumbai, India.”) to the user simulation model. By doing so, we examine whether
explicitly providing demographic indicators to the
model results in simulated users being more aligned
with real users from a given country, relative to
the default simulation setup. For each country,
we ask [ChatGPT](https://chatgpt.com/) to generate typical female and
male names (9 each) that are frequently used and
country-specific, avoiding names common across
multiple countries. For location, we select a major metropolitan city in each country: Mumbai for
India, Nairobi for Kenya, and Lagos for Nigeria.
Using the same procedure as the previous analysis,
we re-run user simulation with the updated prompts
and re-bucket tasks.
We observe some differences in agent performance depending on the country used to simulate users across 5 runs: 55 _._ 6 _±_ 6 _._ 1% for India,
51 _._ 1 _±_ 6 _._ 5% for Kenya, and 47 _._ 8 _±_ 4 _._ 4% for Nigeria. However, there are no apparent stereotypical
linguistic markers or cultural references among interactions from different countries, suggesting that
these differences may stem from more subtle or
implicit cues.
Additionally, we see differences in calibration with and without demographic prompting
(∆ _ECE_ Human–LLM), with negative values indicating better calibration after the intervention. Calibration improves for Indian participants ( _−_ 7 _._ 9),
remains largely unchanged for Nigerian participants (0 _._ 5), and worsens for Kenyan participants
(8 _._ 6). These results suggest that explicitly specifying user identity can influence calibration between simulated and real users in both desirable
and undesirable ways, which is consistent with
prior work showing that demographic prompting

<!-- p:280 -->
14

<!-- p:281 -->
Figure 5: User study chat interface where participants interact with the agent (GPT-4o) to complete tasks.

<!-- p:282 -->
can have mixed effects (Durmus et al., 2024; Sun
et al., 2025). However, more work is needed to
comprehensively investigate the effectiveness and
sensitivity of demographic prompting in agentic
evaluations.

<!-- p:283 -->
15

<!-- p:284 -->
**Bin** **Success** **Example Task**

<!-- p:285 -->
1 0% Your name is User e70 and your zip code is 32190. You just bought a water bottle with 500ml but you regret
it, and you instead want to change it to the other bottle you recently ordered with 1000ml capacity. If the exact
1000ml bottle is not available any more, you can allow the material to be different. To start the conversation,
say ‘Hello, my email is user.e70@example.com.’

<!-- p:286 -->
2 20% You are User l64, and you live in Denver, 80280. You just won a lottery, and you want to upgrade all your
items to the most expensive options (but make sure the shoe is still the same size). You want to pay the
difference with your gift card, but if it is impossible, PayPal is fine. To start the conversation, say ‘Hello, my
email is user.l64@example.com.’

<!-- p:287 -->
3 40% Your name is User u52, and you live in 46236. Your email is user.u52@example.com. You just placed
an order but you realize that your card has only $1131 credit left, and the order total is more than $1160.
You wonder if the agent can help split the payment with another card. If not, you wonder what the most
expensive item is and its price, and if you can just cancel that item. If not, you wonder if you can switch
all items to their cheapest options and bring the cost down to $1131. If so, do it. If not, you wonder if the
agent can just cancel the order so that you can order again. To start the conversation, say ‘Hello, my email is
user.u52@example.com.’

<!-- p:288 -->
4 60% You are User i49, and you live in 32286. You want to exchange your skateboard for a shorter bamboo
material one. If several options are available, you want to know all options and their prices, and choose
the most expensive one because you believe price is quality. Also, you want to exchange the garden hose
you received to the type that you just ordered (pending). To start the conversation, say ‘Hello, my email is
user.i49@example.com.’

<!-- p:289 -->
5 80% You are User b63 in 19122. You received your order #W2378156 and wish to exchange the mechanical
keyboard for a similar one but with clicky switches and the smart thermostat for one compatible with Google
Home instead of Apple HomeKit. If there is no keyboard that is clicky, RGB backlight, full size, you would
rather exchange only the thermostat. You want to make sure everything is addressed in one go. To start the
conversation, say ‘Hello, my email is user.b63@example.com.’

<!-- p:290 -->
6 100% You are User p59, residing in Philadelphia 19031. You want to change the Desk Lamp in order #W9300146
that you’ve placed for the cheapest Desk Lamp that’s available. Any price difference should go to a gift card.
You also want to know how much you get back in total. To start the conversation, say ‘Hello, my email is
user.p59@example.com.’

<!-- p:291 -->
Table 8: Example _τ_ -Bench tasks across difficulty bins. Task difficulty is determined by the percentage of evaluation
runs (out of five) in which the agent succeeds when interacting with simulated users for a given task..

<!-- p:292 -->
16

