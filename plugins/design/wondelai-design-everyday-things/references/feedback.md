# Feedback: Communicating Results Back to the User

Feedback is the information a system sends back to the user after an action. Without feedback, users operate in the dark: they cannot tell whether their action registered, whether it succeeded, or what state the system is in. The absence of feedback is one of the most common and damaging design failures. Every action a user takes must produce a perceivable response.

## Feedback Types

### Visual Feedback

The most common and versatile feedback channel. Visual feedback works for nearly all interactions because users are already looking at the interface.

| Pattern | When to Use | Example |
|---------|------------|---------|
| Color change | State transitions, validation | Button turns green on success, field border turns red on error |
| Animation | Object manipulation, transitions | Item slides off screen when deleted, card flips when toggled |
| Icon change | Status updates, toggle states | Bookmark icon fills in when activated, checkbox gets a checkmark |
| Text update | Confirmations, counts, values | "3 items selected", "Saved at 2:30 PM" |
| Position change | Drag-and-drop, reordering | Item moves to its new position in the list |
| Opacity change | Enable/disable, focus shift | Background dims when a modal opens |

### Auditory Feedback

Sound provides feedback without requiring the user to look at the screen. Useful for confirmations, alerts, and background processes.

| Pattern | When to Use | Example |
|---------|------------|---------|
| Confirmation tone | Action completed successfully | macOS "whoosh" on sent email |
| Error sound | Something went wrong | System alert sound on invalid action |
| Notification chime | New information available | Chat message received sound |
| Typing clicks | Keystroke registration (mobile) | Keyboard tap sounds on iOS |
| Progress tone | Background process advancing | Scanning/processing sound |

**Caution**: Always provide a way to mute sounds. Never rely on sound as the only feedback channel (accessibility requirement). Sound should supplement visual feedback, not replace it.

### Haptic Feedback

Vibration and force feedback on touch devices provide physical confirmation of actions.

| Pattern | When to Use | Example |
|---------|------------|---------|
| Tap confirmation | Button press registered | Short vibration on keypress |
| Selection feedback | Item selected or toggled | Subtle haptic pulse on toggle |
| Error feedback | Action failed or invalid | Sharp double-vibration on error |
| Boundary feedback | Reached end of scrollable content | Rubber-band haptic at scroll edge |
| Success feedback | Major action completed | Strong single pulse on "Order Placed" |

### Progress Feedback

Communicates advancement toward completion during longer operations.

| Pattern | When to Use | Duration Context |
|---------|------------|-----------------|
| Determinate progress bar | Duration is known/estimable | File upload, multi-step process |
| Indeterminate spinner | Duration is unknown | Network request, search |
| Skeleton screen | Content is loading | Page or section load |
| Percentage text | Precise progress matters | "Uploading: 67% complete" |
| Step indicator | Multi-phase process | "Step 2 of 4: Payment" |
| Elapsed time counter | Very long operations | "Processing... 3m 22s elapsed" |

---

## Response Time Guidelines

These thresholds, established by usability research (Miller 1968, Card et al. 1983, Nielsen 1993), define user expectations for system response.

| Threshold | User Perception | Required Feedback |
|:---------:|----------------|-------------------|
| **0 - 100ms** | Instantaneous. Action feels directly connected to result. | Direct visual change (color, position, state). No loading indicator needed. |
| **100ms - 1s** | Noticeable delay. Still feels responsive but the system is "thinking." | Show cursor change or subtle animation. No spinner needed yet. |
| **1s - 10s** | Significant delay. User's attention begins to wander. | Show spinner or progress indicator. Keep the user informed that work is happening. |
| **10s - 60s** | Long wait. User may switch tasks. | Show progress bar with percentage or estimated time. Allow the operation to continue in the background. |
| **> 60s** | Very long wait. User may assume failure. | Show progress, elapsed time, and estimated remaining time. Send a notification when complete. Allow the user to navigate away. |

### Response Time by Interaction Type

| Interaction | Expected Response Time | Feedback Strategy |
|-------------|:---------------------:|-------------------|
| Button click | < 100ms | Instant visual state change |
| Form field validation | < 300ms after typing stops | Inline validation message |
| Page navigation | < 1s | Skeleton screen or loading bar |
| Search results | < 2s | Skeleton screen with animated placeholder |
| File upload (small) | 1-5s | Progress bar |
| File upload (large) | 5-60s+ | Progress bar with percentage and cancel button |
| Data export | 10s-5min | Background process with notification on completion |
| Account creation | < 3s | Full-screen success state |

---

## Feedback Patterns by Interaction Type

### Click / Tap Feedback

| State | Visual Feedback | Purpose |
|-------|----------------|---------|
| Hover | Background color change, cursor change | "This is interactive" |
| Active (pressed) | Darker color, slight scale-down | "Your click registered" |
| Loading | Spinner replaces label, or button shows loading state | "Processing your request" |
| Success | Checkmark icon, color change to green, or toast message | "Action completed" |
| Error | Shake animation, red color, or inline error message | "Something went wrong" |

### Form Submission Feedback

| Stage | Feedback | Implementation |
|-------|----------|---------------|
| Validation (inline) | Green checkmark or red error per field | Show as user completes each field |
| Submission initiated | Button shows loading state, form inputs disabled | Prevent duplicate submissions |
| Success | Toast notification, redirect, or inline success message | "Your changes have been saved" |
| Partial success | Yellow warning with details | "Saved, but 2 fields need attention" |
| Failure | Inline errors at fields, summary at top, form data preserved | Never erase user input on error |

### Drag and Drop Feedback

| Stage | Feedback | Purpose |
|-------|----------|---------|
| Drag start | Element lifts (shadow increase), ghost follows cursor | "You are holding this" |
| Drag over valid target | Drop zone highlights (border, background) | "You can drop here" |
| Drag over invalid target | No highlight, or red border, cursor shows "not-allowed" | "You cannot drop here" |
| Drop | Element animates to new position, drop zone returns to normal | "Placed successfully" |
| Cancel (drop outside) | Element animates back to original position | "Action cancelled, nothing changed" |

### Loading State Patterns

| Pattern | Best For | Description |
|---------|----------|-------------|
| **Spinner** | Unknown duration, small area | Rotating circle or dots. Simple but uninformative. |
| **Skeleton screen** | Page or section loads | Gray placeholder shapes matching content layout. Feels faster than a spinner. |
| **Progress bar (determinate)** | Known duration | Fills from left to right. Best when you can calculate progress. |
| **Progress bar (indeterminate)** | Unknown duration, larger area | Bar animates back and forth. Better than spinner for larger regions. |
| **Percentage text** | Long operations | "43% complete" gives precise expectation. |
| **Shimmer effect** | Content cards, lists | Gradient animation flowing across placeholder shapes. |

### Error Feedback

| Principle | Implementation |
|-----------|---------------|
| Say what went wrong | "Your password must be at least 8 characters" not "Invalid input" |
| Say how to fix it | "Add 3 more characters to your password" |
| Do not blame the user | "That email address is not registered" not "You entered a wrong email" |
| Preserve user's work | Never clear a form on error. Show errors inline and let users fix them. |
| Use appropriate severity | Red and bold for blocking errors. Yellow for warnings. Gray for hints. |
| Place errors near the source | Inline errors below the relevant field. Summary at the top for multiple errors. |

### Error Message Template

```
[Icon] [What happened]
[Why it happened - optional, if it helps]
[How to fix it]
[Alternative action - optional]
```

**Example**:
```
[!] We could not process your payment.
Your card was declined by the issuing bank.
Please try a different card or contact your bank.
[Try a different payment method]
```

### Success Feedback

| Pattern | When to Use | Example |
|---------|------------|---------|
| **Toast notification** | Non-critical confirmations | "Settings saved" (auto-dismiss after 4s) |
| **Inline success message** | Form submissions | Green banner: "Your profile has been updated" |
| **Full-screen celebration** | Major milestones | Confetti animation on completing onboarding |
| **Redirect with flash** | After creating something | Redirect to the new item with a "Created successfully" banner |
| **Subtle state change** | Toggle/minor actions | Star icon fills in, count increments |
| **Email/notification** | Background processes | "Your export is ready" email with download link |

---

## Too Much vs. Too Little Feedback

### Too Little Feedback

| Symptom | User Impact | Fix |
|---------|-------------|-----|
| Click produces no visible change | User clicks again, causing duplicates | Add immediate visual state change on click |
| Form submits with no confirmation | User resubmits, or navigates away unsure | Show success toast or redirect to confirmation |
| Background save with no indicator | User manually saves repeatedly | Show "Saved" indicator with timestamp |
| Error fails silently | User believes action succeeded | Always show errors explicitly |
| Long process with no progress | User assumes system is frozen | Show progress indicator for any operation > 1 second |

### Too Much Feedback

| Symptom | User Impact | Fix |
|---------|-------------|-----|
| Alert dialog for every action | User develops "dialog blindness" and clicks OK without reading | Use toasts for non-critical feedback, reserve dialogs for critical confirmations |
| Sound on every click | Annoying, especially in shared spaces | Use sound sparingly, only for important events |
| Animation on every state change | Interface feels hyperactive and distracting | Limit animation to meaningful transitions |
| Multiple notification channels for one event | Email + push + in-app + SMS overwhelms | Let users choose notification channels |
| Confirmation toast that blocks content | User must dismiss it before continuing | Use non-blocking toast that auto-dismisses |

### The Feedback Balance Rule

- Every action needs *some* feedback.
- Not every action needs *prominent* feedback.
- Match feedback prominence to action importance.

| Action Importance | Feedback Prominence |
|:-----------------:|:-------------------:|
| Critical (delete account, payment) | Modal dialog, full-screen confirmation |
| Important (save, submit, send) | Toast notification, inline confirmation |
| Routine (click, select, toggle) | Subtle visual state change |
| Ambient (auto-save, sync) | Tiny indicator, no interruption |

---

## Feedback in Accessibility Context

| User Group | Requirements |
|-----------|-------------|
| **Screen reader** | ARIA live regions for dynamic updates; `role="alert"` for errors; progress announcements; focus moves to new messages |
| **Keyboard-only** | Visible focus rings; focus moves to resulting content after actions; loading states trap focus appropriately |
| **Low-vision** | Color paired with icon and text; animations paired with text messages; WCAG 4.5:1 contrast |
| **Motion-sensitive** | `prefers-reduced-motion` alternatives; no aggressive pulsing; avoid parallax and spinning |

---

## Feedback Audit Checklist

### Presence

- [ ] Every clickable element has a visible response within 100ms.
- [ ] Every form submission produces explicit success or error feedback.
- [ ] Every operation longer than 1 second shows a loading indicator.
- [ ] Every error displays a human-readable message with remediation steps.
- [ ] State changes (toggle, selection, mode) produce visible feedback.

### Timing

- [ ] Direct manipulation feedback is under 100ms.
- [ ] Inline validation fires within 300ms after the user stops typing.
- [ ] Spinners appear within 1 second of starting a long operation.
- [ ] Toast messages auto-dismiss in 4-8 seconds (with a way to dismiss manually or keep visible).
- [ ] Background operations notify the user upon completion.

### Appropriateness

- [ ] Critical actions produce prominent feedback (modal, full-screen).
- [ ] Routine actions produce subtle feedback (state change, micro-animation).
- [ ] No unnecessary alert dialogs for routine confirmations.
- [ ] Sound feedback has a mute option.
- [ ] Feedback does not block the user's primary workflow.

### Accessibility

- [ ] ARIA live regions announce dynamic feedback for screen readers.
- [ ] Focus moves to error messages or success messages as appropriate.
- [ ] Color is not the only feedback channel (icons, text, borders also used).
- [ ] Animations have reduced-motion alternatives.
- [ ] Error messages identify which field has the problem.

### Content

- [ ] Error messages say what went wrong, why, and how to fix it.
- [ ] Success messages confirm what was done.
- [ ] Progress indicators show meaningful advancement (not just spinning).
- [ ] System state is visible at all times (connection status, save status, mode).

---

## Examples of Excellent and Poor Feedback

### Excellent: Gmail Undo Send

After clicking Send, Gmail shows a toast: "Message sent. Undo." The toast persists for a configurable number of seconds. The user has visual confirmation (message sent) and an immediate recovery option (undo). Feedback and error recovery in a single, unobtrusive element.

### Excellent: Stripe Payment Form

As the user types a credit card number, the form identifies the card type (Visa, Mastercard) and displays the logo. Invalid digits are rejected in real-time. The expiration date auto-formats. Errors appear inline below each field. The submit button shows a spinner during processing and a checkmark on success. Every stage of the interaction has clear, immediate feedback.

### Poor: Silent Form Submission

A contact form has a "Submit" button. The user clicks it. Nothing happens for 3 seconds, then the page reloads and the form is empty. Did the message send? The user has no way to know. They may submit again, creating duplicates, or leave without confidence.

### Poor: Aggressive Alert Dialogs

An enterprise application shows an alert dialog for every action: "Are you sure you want to save?" "Save successful!" "Are you sure you want to navigate away?" Users click OK/Yes on every dialog without reading them, which means when a truly important confirmation appears (like permanent deletion), it is dismissed reflexively.

### Poor: Invisible Background Sync

A note-taking app syncs to the cloud in the background but provides no indicator. The user edits a note, closes the app, and opens it on another device expecting to see the changes. The sync had not completed. No feedback was ever given about sync status, so the user had no way to know.
