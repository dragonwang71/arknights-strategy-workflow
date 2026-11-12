# Design notes

[← Project overview](../README.md)

The local application connects planning, validation, and execution. These notes explain the decisions behind that workflow and the small component available in this repository.

## Validate the artifact that will be used

A successful trial is useful evidence, but the user ultimately executes a saved plan. Saving, reloading, and replaying that plan therefore form a separate check.

| Step | Question |
| :--- | :--- |
| Trial | Can this candidate complete the task in the trial environment? |
| Saved-plan replay | Does the saved artifact reproduce that behavior? |
| Independent validation | Does it still pass under fresh conditions and previously observed failures? |
| Game execution | Does the saved plan work through the actual execution path? |

Passing one step does not establish the next. The local prototype has completed practice execution in tested setups; that does not prove universal stage support or exact equivalence between every offline and live configuration. The public sample covers candidate generation only.

## Keep failures useful when work resumes

One local candidate passed its initial trial and saved-plan replay, then failed an independent replay. The candidate was rejected. The plan and execution settings were held constant while the random condition changed.

That case exposed a continuation problem: retaining the failing random condition was not enough. To use the failure when refining the plan, the next session also needed the complete diagnostic record.

The fix restored the complete failure record only when it matched the saved plan and execution settings. Checks confirmed that valid records could be restored and incomplete or mismatched records were rejected. This establishes a specific continuation behavior; it does not establish a higher overall success rate or learning across tasks.

The distinction matters in any iterative workflow: **being able to repeat a failure and being able to act on its evidence are separate capabilities.**

## Make a narrow proposal, then evaluate it

The [timing module](../strategy_workflow/timing.py) was extracted from the local project's planning logic. It addresses a specific failure pattern: a withdrawn operator becomes available again too late.

Before proposing a change, it checks for supporting observations: a matching withdrawal, an unavailable deployment, sufficient recorded resources, and a failure before the eventual return. Missing or contradictory evidence results in no proposal.

The module can:

- Shorten a positive wait before withdrawal.
- Move withdrawal ahead of independent actions without crossing recorded dependency or event barriers.

It preserves the original input and the constraints attached to the actions. It cannot tell whether earlier withdrawal will weaken another part of the battle, so its output remains a set of candidates for a separate evaluator.

The [synthetic example](../examples/timing_case.json) uses abstract roles and observations. The [tests](../tests/test_timing.py) cover evidence checks, action preservation, and barriers to reordering. The input field `native_conditions` is treated as an opaque event constraint; no game runtime is included or called.

## Keep the public example self-contained

The sample uses only the Python standard library. It demonstrates actual extracted planning logic without depending on account records, game assets, or the local execution environment.

The wider prototype uses reference strategies, constrained search, and feedback. AI coding tools assisted development; an LLM is not required to select each action during normal operation. Component attribution and publication terms are in [NOTICE.md](../NOTICE.md).
