# N5 development campaign spend notice

Date: 2026-09-25. Credential method: Claude Code's Claude.ai subscription
inside the attested WSL worker host. The campaign has not been launched.

The proposed schedule contains **36 task episodes**: 12 synthetic development
tasks, each on B0, task-sensitive candidate and predeclared alternative arms.
Each episode has one USD 3 root allocation covering up to three serial worker
attempts. The sum of **local admission allocations is USD 108**. These
allocations prevent the scheduler from starting a new episode without reserved
funds. They cannot guarantee that an in-flight provider call stops billing at
its allocation. There are no automatic replays of uncertain calls, and a
budget breach blocks the campaign.

The direct API-equivalent planning range is **USD 10–60** and elapsed time is
**2–8 hours**, including WSL staging, worker time, isolated public checks and
hidden grading. This is a low-confidence projection, not a subscription
invoice or charge cap. It extrapolates from the completed 60-call screen
(USD 7.410898 reported API-equivalent cost; 2,081.827 seconds summed call
time; about 100 minutes elapsed) while allowing roughly 2–5 times more
work per new task and up to three attempts on a failed root. The tasks and
model mix differ materially from that screen. Fable's current per-task cost
is especially uncertain. No cache reuse across model switches is assumed.

At the [Anthropic pricing page](https://platform.claude.com/docs/en/about-claude/pricing),
checked 2026-09-25, standard Sonnet 5 input/output are USD 2/10 per million
tokens, Opus 5 USD 5/25 and Fable 5.1 USD 10/50. Five-minute cache-write rates
are USD 2.50, 6.25 and 12.50; cache-read rates are USD 0.20, 0.50 and 0.25,
respectively. The projection assumes approximately 36–80 total model calls,
each with 0–10,000 ordinary input tokens, 1,500–15,000 cache-write tokens,
20,000–100,000 cache-read tokens and 300–8,000 output tokens. This broad mix,
the observed screen receipts and operational overhead motivate the range;
large output, retries or provider behaviour outside these assumptions can
exceed it. Receipt costs, usage categories and elapsed time will be reported
after the run. Unknown subscription billing impact is not represented as zero.

The immutable manifest must bind this notice's SHA-256, the current WSL host,
subscription and Read-denial sentinel evidence, the complete screen record,
every public and reserved corpus file, source dependencies, exact row order,
assessments and per-episode ceilings. The runner must validate an approval
record naming that exact manifest digest and USD 108 allocation before its
first provider side effect. The earlier USD 48.75 screen approval does not
cover this development campaign.
