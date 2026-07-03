# CoreWeave Cordon Rules: the node-lifecycle controller owns the cordon

**Last verified: 2026-07-02.**

**Primary source:** CoreWeave Kubernetes node lifecycle & health documentation —
<https://docs.coreweave.com/> (Node Lifecycle / Node Health sections). Kubernetes
cordon/drain semantics: <https://kubernetes.io/docs/concepts/architecture/nodes/>.

## The hard rule

> **Never manually uncordon a CoreWeave health cordon.** When CoreWeave's
> node-lifecycle controller detects a hardware fault (via Xid events, DCGM health
> checks, or NVLink/NVSwitch errors), it **cordons** the node and drives it through
> an automated remediation path — reset, reboot, or replacement. That cordon is
> **owned by the controller.** A human running `kubectl uncordon` on it re-admits
> pods onto known-bad hardware and races the controller's own actions.

`triage.py` attaches this rule (`cordon_rule`) to every verdict whose action is a
hardware move — `reset-gpu`, `reboot-node`, or `rma`. It is surfaced in the CORDON
line of the verdict block precisely so an operator under run-is-dying pressure
does not "unstick" a node by uncordoning it.

## Cordon provenance: whose cordon is it?

Not every cordon is a health cordon. Before touching a node's schedulability,
determine who cordoned it:

```bash
kubectl get node <node> -o json | jq '{unschedulable: .spec.unschedulable, taints: .spec.taints}'
kubectl describe node <node> | sed -n '/Taints:/,/Unschedulable/p'
```

| Cordon source | Who owns it | Your move |
|---|---|---|
| CoreWeave health cordon (controller taint) | The lifecycle controller | **Leave it.** Let remediation run. |
| Your own maintenance cordon | You | Uncordon when your maintenance is done. |
| A batch scheduler's drain (SUNK/Slurm-on-K8s, Kueue) | The scheduler | Manage via the scheduler, not raw kubectl. |

> **[unverified]** CoreWeave's exact taint **key/value** and node-condition label
> for a health cordon are **not fully published** and may change between cluster
> versions. Identify a controller-owned cordon by its provenance (a
> non-user-applied taint appearing right after an Xid/DCGM event), and when in
> doubt, ask CoreWeave support rather than uncordoning.

## The safe operator path per action

The skill **recommends** these; it does not execute cordon/drain/reset itself
(scoped, read-only tools only — see the skill's `allowed-tools`).

- **`reschedule` (Xid 94):** no node action. Restart the failed rank; the node
  stays schedulable. If your scheduler already evicted the pod, just resubmit.
- **`reset-gpu` (Xid 95 / 48 / 74 / 119 / 120, remap pending):** drain the
  affected pods, reset the GPU (`nvidia-smi -r`) or let the controller reset the
  node. Do not fight a health cordon if the controller already placed one.
- **`reboot-node` (Xid 79):** the card is off the bus — only a bare-metal reboot
  brings it back. Expect the controller to cordon and reboot; **let it.** Do not
  uncordon to "save" the node before the reboot completes.
- **`rma` (Xid 64 / remap failure):** terminal. The controller cordons and pulls
  the node for replacement. Open/confirm the RMA with CoreWeave support; never
  uncordon a card queued for replacement.

## Why this matters for a training run

On a multi-node job, one bad GPU stalls the whole collective. The instinct under
pressure is to uncordon the node and get the job moving again. On a **health**
cordon that is exactly wrong: you re-admit the run onto the failing card, and the
next Xid kills it again — now having burned more GPU-hours. The correct move is to
let the controller replace the node and reschedule the run onto healthy hardware.
