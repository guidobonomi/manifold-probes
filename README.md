# manifold-probes

Throwaway Claude Code plugin marketplace used to test enforcement surfaces for PRD-124.

`manifold-block-probe` denies one prompt and one tool call, matched on a single marker in
a specific payload field, and logs the payload shape it received to
`/tmp/manifold-block-probe.log`. It blocks nothing else, reads nothing, and sends nothing.

Not for production use.
