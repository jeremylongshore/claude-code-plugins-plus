# iOS Keyboard & Input Patterns

Comprehensive guide to keyboard handling, text input, and hardware keyboard support.

## Software Keyboard Types

### Choosing the Right Keyboard

Match the keyboard to the expected input:

| Input Type | Keyboard | UIKeyboardType |
|------------|----------|----------------|
| General text | Default | `.default` |
| Email | Email-optimized (@ and . prominent) | `.emailAddress` |
| URL | URL-optimized (/, .com) | `.URL` |
| Phone number | Number pad | `.phonePad` |
| Numeric (with punctuation) | Numbers + punctuation | `.numbersAndPunctuation` |
| Numeric only | Decimal pad | `.decimalPad` |
| Twitter handle | Twitter keyboard | `.twitter` |
| Web search | Search keyboard | `.webSearch` |
| ASCII only | ASCII-capable | `.asciiCapable` |

### SwiftUI Implementation

```swift
TextField("Email", text: $email)
    .keyboardType(.emailAddress)
    .textContentType(.emailAddress)
    .autocapitalization(.none)
    .disableAutocorrection(true)
```

### UIKit Implementation

```swift
textField.keyboardType = .emailAddress
textField.textContentType = .emailAddress
textField.autocapitalizationType = .none
textField.autocorrectionType = .no
```

---

## Text Content Types

Enable autofill by specifying content types:

| Content | textContentType | Enables |
|---------|-----------------|---------|
| Name | `.name` | Contact autofill |
| Given name | `.givenName` | |
| Family name | `.familyName` | |
| Email | `.emailAddress` | Email autofill |
| Phone | `.telephoneNumber` | Phone autofill |
| Address | `.streetAddressLine1` | Address autofill |
| City | `.addressCity` | |
| State | `.addressState` | |
| ZIP | `.postalCode` | |
| Country | `.countryName` | |
| Credit card | `.creditCardNumber` | Camera card scanning |
| Username | `.username` | Keychain autofill |
| Password | `.password` | Keychain autofill |
| New password | `.newPassword` | Password generation |
| One-time code | `.oneTimeCode` | SMS autofill |

### Password and Login Fields

```swift
// Login form
TextField("Email", text: $email)
    .textContentType(.username)
    .keyboardType(.emailAddress)

SecureField("Password", text: $password)
    .textContentType(.password)

// Registration form
SecureField("Create Password", text: $newPassword)
    .textContentType(.newPassword)
```

### One-Time Code (2FA)

```swift
TextField("Verification Code", text: $code)
    .textContentType(.oneTimeCode)
    .keyboardType(.numberPad)
```

iOS automatically suggests codes from SMS messages when this content type is set.

---

## Input Accessory Views

### When to Use

Input accessory views appear above the keyboard for:
- Navigation between fields (Previous/Next)
- Custom actions (Done, formatting buttons)
- Context-specific tools

### Standard Toolbar Pattern

```swift
struct FormTextField: View {
    @Binding var text: String
    @FocusState private var isFocused: Bool

    var body: some View {
        TextField("Value", text: $text)
            .focused($isFocused)
            .toolbar {
                ToolbarItemGroup(placement: .keyboard) {
                    Spacer()
                    Button("Done") {
                        isFocused = false
                    }
                }
            }
    }
}
```

### Multi-Field Navigation

```swift
struct FormView: View {
    @FocusState private var focusedField: Field?

    enum Field {
        case firstName, lastName, email
    }

    var body: some View {
        Form {
            TextField("First Name", text: $firstName)
                .focused($focusedField, equals: .firstName)

            TextField("Last Name", text: $lastName)
                .focused($focusedField, equals: .lastName)

            TextField("Email", text: $email)
                .focused($focusedField, equals: .email)
        }
        .toolbar {
            ToolbarItemGroup(placement: .keyboard) {
                Button(action: focusPrevious) {
                    Image(systemName: "chevron.up")
                }
                .disabled(!canFocusPrevious)

                Button(action: focusNext) {
                    Image(systemName: "chevron.down")
                }
                .disabled(!canFocusNext)

                Spacer()

                Button("Done") {
                    focusedField = nil
                }
            }
        }
    }
}
```

---

## Keyboard Avoidance

### Automatic Behavior (SwiftUI)

SwiftUI automatically adjusts for keyboard in most cases:
- ScrollViews scroll to keep focused field visible
- Safe area adjusts for keyboard height

### Manual Keyboard Handling

```swift
struct KeyboardAdaptive: ViewModifier {
    @State private var keyboardHeight: CGFloat = 0

    func body(content: Content) -> some View {
        content
            .padding(.bottom, keyboardHeight)
            .onReceive(Publishers.keyboardHeight) { height in
                withAnimation(.easeOut(duration: 0.25)) {
                    keyboardHeight = height
                }
            }
    }
}
```

### Best Practices

1. **Scroll to show field** - Focused field should be visible
2. **Don't cover important actions** - Submit buttons should remain accessible
3. **Animate adjustments** - Match keyboard animation (0.25s ease-out)
4. **Test on different devices** - Keyboard heights vary

---

## Hardware Keyboard Support

### Why It Matters

iPads commonly use hardware keyboards. Apps should:
- Support standard keyboard shortcuts
- Provide discoverability
- Not break when hardware keyboard is attached

### Standard Shortcuts to Support

| Shortcut | Action | Notes |
|----------|--------|-------|
| ⌘N | New item | Standard creation |
| ⌘S | Save | |
| ⌘⌫ | Delete | With confirmation |
| ⌘F | Find/Search | |
| ⌘Z | Undo | |
| ⌘⇧Z | Redo | |
| ⌘C/⌘V/⌘X | Copy/Paste/Cut | |
| ⌘, | Settings/Preferences | |
| ⌘W | Close window/modal | |
| Escape | Cancel/dismiss | |
| Tab | Next field | |
| ⇧Tab | Previous field | |
| Return | Submit form | When appropriate |

### SwiftUI Keyboard Shortcuts

```swift
struct ContentView: View {
    var body: some View {
        NavigationStack {
            ItemList()
                .toolbar {
                    Button("New Item", action: createItem)
                        .keyboardShortcut("n", modifiers: .command)
                }
        }
    }
}

// For custom shortcuts in list items
List {
    ForEach(items) { item in
        ItemRow(item: item)
    }
}
.onDeleteCommand(perform: deleteSelected)  // ⌘⌫
```

### Keyboard Shortcut Discoverability

Hold ⌘ to show available shortcuts. Ensure your shortcuts appear:

```swift
Button("Save", action: save)
    .keyboardShortcut("s", modifiers: .command)
    // Appears in keyboard shortcut overlay
```

---

## Text Editing

### Autocapitalization

| Style | Use For |
|-------|---------|
| `.sentences` | General text, messages |
| `.words` | Names, titles |
| `.allCharacters` | Codes, abbreviations |
| `.none` | Email, usernames, URLs |

### Autocorrection

| Setting | Use For |
|---------|---------|
| Enabled (default) | Prose, messages |
| Disabled | Code, usernames, specific values |

```swift
TextField("Username", text: $username)
    .autocapitalization(.none)
    .disableAutocorrection(true)
```

### Text Input Traits Summary

```swift
TextField("Email", text: $email)
    .keyboardType(.emailAddress)      // Keyboard layout
    .textContentType(.emailAddress)   // Autofill hint
    .autocapitalization(.none)        // No auto-caps
    .disableAutocorrection(true)      // No autocorrect
    .textInputAutocapitalization(.never) // iOS 15+
```

---

## Secure Text Entry

### Password Fields

```swift
SecureField("Password", text: $password)
    .textContentType(.password)
```

### Show/Hide Toggle Pattern

```swift
struct PasswordField: View {
    @Binding var password: String
    @State private var isSecure = true

    var body: some View {
        HStack {
            if isSecure {
                SecureField("Password", text: $password)
            } else {
                TextField("Password", text: $password)
            }

            Button(action: { isSecure.toggle() }) {
                Image(systemName: isSecure ? "eye.slash" : "eye")
                    .foregroundColor(.secondary)
            }
        }
        .textContentType(.password)
    }
}
```

---

## Search Input

### Search Field Behavior

```swift
struct SearchView: View {
    @State private var searchText = ""

    var body: some View {
        NavigationStack {
            List(filteredItems) { item in
                ItemRow(item: item)
            }
            .searchable(
                text: $searchText,
                placement: .navigationBarDrawer(displayMode: .always),
                prompt: "Search items"
            )
        }
    }
}
```

### Search Suggestions

```swift
.searchable(text: $searchText) {
    ForEach(suggestions) { suggestion in
        Text(suggestion.name)
            .searchCompletion(suggestion.name)
    }
}
```

---

## Common Patterns

### Form with All Best Practices

```swift
struct RegistrationForm: View {
    @State private var email = ""
    @State private var password = ""
    @State private var confirmPassword = ""
    @FocusState private var focusedField: Field?

    enum Field: Hashable {
        case email, password, confirmPassword
    }

    var body: some View {
        Form {
            Section("Account") {
                TextField("Email", text: $email)
                    .keyboardType(.emailAddress)
                    .textContentType(.username)
                    .autocapitalization(.none)
                    .disableAutocorrection(true)
                    .focused($focusedField, equals: .email)
                    .submitLabel(.next)
                    .onSubmit { focusedField = .password }

                SecureField("Password", text: $password)
                    .textContentType(.newPassword)
                    .focused($focusedField, equals: .password)
                    .submitLabel(.next)
                    .onSubmit { focusedField = .confirmPassword }

                SecureField("Confirm Password", text: $confirmPassword)
                    .textContentType(.newPassword)
                    .focused($focusedField, equals: .confirmPassword)
                    .submitLabel(.done)
                    .onSubmit(register)
            }

            Section {
                Button("Create Account", action: register)
            }
        }
        .toolbar {
            ToolbarItemGroup(placement: .keyboard) {
                Button("Previous") { moveFocus(-.previous) }
                Button("Next") { moveFocus(.next) }
                Spacer()
                Button("Done") { focusedField = nil }
            }
        }
    }
}
```

### Submit Label Options

| Label | Use For |
|-------|---------|
| `.done` | Final field, closes keyboard |
| `.go` | Triggers action (search, navigate) |
| `.next` | Moves to next field |
| `.return` | Inserts newline (text areas) |
| `.search` | Search field |
| `.send` | Message composition |
| `.continue` | Multi-step forms |
| `.join` | Joining/connecting |
| `.route` | Navigation apps |

```swift
TextField("Search", text: $query)
    .submitLabel(.search)
    .onSubmit { performSearch() }
```
