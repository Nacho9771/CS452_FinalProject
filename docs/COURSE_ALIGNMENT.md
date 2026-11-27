# CS 452 concepts in My Kitchen

Reviewed November 26, 2026. The product requirements remain in `AppFlow.md` and
`README.md`; this document connects the implementation to course concepts.

## What was accessible

Using read-only Canvas API requests, reviewed the syllabus, nine modules and their
items, assignment instructions (71 records), and 19 module-linked pages. The general
Pages listing returned 404, but individual module-linked pages were accessible.
The Files listing returned 403. Embedded external assessments with empty Canvas
descriptions, file contents, Teams recordings, external videos, and every linked
notebook have not been reviewed. This is a course-content scan, not a claim to know
which assignments the student completed or everything said in lectures.

Also read the instructor's linked Redis work-queue instructions, Mongo learning
plan, pipeline project instructions, and reliability/scaling/system-design activities.
The original teaching material is not copied into the public project documentation.
The local Canvas reference is `.local/canvas-course.json`, excluded from Git.

## Map the concepts to actual app behavior

| Course concept | Application to My Kitchen | Implementation status |
|---|---|---|
| Data modeling: keys, relationships, optionality | Distinguish account, kitchen, recipe, planned meal, and cooking event. Ask what one record represents and what makes it unique. | Recipe input contract only; persistence model is next. |
| State versus event (Sept 28 design class) | A scheduled recipe is current state; cooking/skipping it is an event. Moving a dinner must not falsely record it as cooked. | Planned. |
| SQL aggregation, joins, subqueries, windows | Questions such as most-cooked meals, last cooking date, ratings over time, and combined shopping quantities. With MongoDB, apply the same grouping/filtering concepts through its query/aggregation API. | Planned; no extra SQL service required for the current MongoDB direction. |
| Complex types and MongoDB | Embed bounded recipe ingredients/steps; keep growing cooking history separate. Document when to embed and when to reference. | Python validates nested JSON; no database connected. |
| Data storage and indexes | Start from queries: recipes owned by an account, dinners in a date range, recent cooking events. Add indexes for demonstrated access patterns. | Planned. |
| Transactions and concurrency | Two devices editing one meal plan must not overwrite each other silently. Use a revision in conditional updates and return a conflict when it no longer matches. | Planned; validate with competing writes when persistence lands. |
| Redis queue and multiple workers | Long recipe-search/meal-planning work becomes a job; a worker claims it and saves status/result. Test worker crashes and repeated delivery. | Planned; Redis does not execute Python by itself. |
| Polling versus notifications | A status endpoint is the simple first client contract. Notifications can reduce waiting overhead, but saved status must remain recoverable if a notification is missed. | Planned. |
| Unified logging | Follow one request using an identifier instead of guessing which console line belongs to it. Later propagate job IDs across API and worker. | API request IDs and completion logs implemented. |
| Embeddings and podcast recommendation | Potential semantic recipe retrieval or similar-recipe search. Compare results against simple filters before adopting embeddings; use the same embedding model for query and corpus. | Optional future integration, not a dependency for the first workflow. |
| RAG and access control | Retrieve recipe facts before explaining them; enforce private-recipe access before supplying context to AI. | Planned; Firebase identity and server-side ownership checks remain required. |
| ETL and data pipelines | Fetch recipes/prices, normalize ingredient identities and units, validate, deduplicate, and save provenance and observation time. Repeated imports should update rather than duplicate. | Planned; the Canvas helper is a separate development-only example of extraction and pagination. |
| Reliability, scaling, security boundaries | Separate mobile UI, API, lasting storage, temporary cache, and workers. Explain what fails when each is unavailable; protect credentials and measure before adding replicas. | Boundaries documented; remote services not connected. |
| Graph databases, Spark, Kusto, warehouses | Useful class concepts for relationship-heavy traversal or large-scale analytics if the app eventually needs them. | No present requirement justifies adding these services to the app. |

These mappings are design recommendations, not claims that class instructions
require every technology in this project. The final-project page permits varied
storage choices and requires a project that reads and writes data.

## Backend build sequence and learning checkpoints

1. **Local request and calculation foundation (current):** send the example JSON,
   inspect validation errors, step through scaling, and match response/log IDs.
   Explain why Python performs arithmetic and why weight/volume needs density.
2. **Identity and lasting account/kitchen records:** Firebase Google sign-in on the
   client, token verification on the API, MongoDB storage, explicit ownership, and
   resumable onboarding. Verify that account A cannot read or update account B.
   Explain the difference between authentication and authorization.
3. **Private manual recipe read/write:** save recipes with server-derived ownership,
   list/read/update them, and introduce conditional revisions. A test must demonstrate
   both persistence and a stale-edit conflict. Define publication separately.
4. **External discovery:** prove a usable source, normalize into the recipe contract,
   retain original text/source, and implement constraint filtering and ranking.
   Explain which facts come from the provider and which decisions come from our code.
5. **Calendar and feedback:** implement planned/cooked/skipped actions, movement,
   saves/likes, and history without confusing state with events.
6. **Combined-list pricing and planning jobs:** prove one store data source, settle
   package/quantity rules, calculate costs in Python, and introduce Redis workers
   and model assistance. Demonstrate a worker crash, retry, and duplicate-write guard.
7. **Operational checks:** keep evidence of failover behavior, actual hosting costs,
   performance, and any synchronization limitations. Extend the app incrementally.

At each step, `DEVELOPMENT.md` must include the runnable request, the code path,
how to change it, what can fail, and the actual checks run. Infrastructure boxes
become implemented only when the real connection has been demonstrated.

## Course deliverables and date correction

Canvas's `due_at` for **Final Project and Report** and **Final Project Collaboration
and Reviews** is `2026-12-11T06:59:59Z`: **December 10, 2026, 11:59 p.m. Mountain
Time**. This differs from the historical December 3 planning horizon in
`INITIAL_DESIGN.md`. The student's individual presentation date is not established
by this review. Recheck Canvas before submission.

The final-project page specifies 30–40 hours and reading/writing data. The report
assignment asks for a GitHub Markdown report with summary, diagrams, demo, at least
three learnings, AI integration and AI-development disclosure, personal motivation,
and applicable reliability/scaling/performance/authentication/concurrency discussion.
It also asks for a class-channel post link and a choice about sharing the project.
The collaboration assignment specifies at least three collaborative hours and a PDF
report. This review creates no submissions and records no completed hours.

The stateless preview API alone does not yet fulfill the final project's lasting
read/write workflow; account/kitchen persistence is the next integration milestone.

## Sources and refreshing the local reference

- [Course modules](https://byu.instructure.com/courses/35462/modules)
- [Database design: relationships and subtypes](https://byu.instructure.com/courses/35462/pages/in-class-9-slash-28-database-design-relationships-and-subtypes)
- [Embeddings](https://byu.instructure.com/courses/35462/pages/in-class-10-slash-14-embeddings)
- [Redis assignment](https://byu.instructure.com/courses/35462/assignments/1472743)
- [Redis example](https://github.com/byu-cs-452/byu-cs-452-class-content/blob/main/redis/work_queue_example/readme.md)
- [Mongo learning plan](https://github.com/byu-cs-452/byu-cs-452-class-content/blob/main/mongo/README.md)
- [Pipeline project](https://github.com/byu-cs-452/byu-cs-452-class-content/blob/main/pipeline/build_a_pipeline.md)
- [System design activity](https://github.com/byu-cs-452/byu-cs-452-class-content/blob/main/system_design/System_Design.md)
- [Final project](https://byu.instructure.com/courses/35462/pages/final-project-2)
- [Final report assignment](https://byu.instructure.com/courses/35462/assignments/1472720)
- [Collaboration assignment](https://byu.instructure.com/courses/35462/assignments/1472718)

To refresh the Canvas snapshot, with the key already configured as a Windows user
environment variable:

```powershell
$env:CANVAS_API_KEY = [Environment]::GetEnvironmentVariable('CANVAS_API_KEY', 'User')
uv run python scripts/review_canvas.py
```

This helper reads course content only; it is not part of the mobile backend and
the app has no Canvas dependency. It never writes to Canvas. Do not paste the key
into source files, example requests, logs, or documentation. Check its printed
availability summary before assuming a refresh covered every resource.
