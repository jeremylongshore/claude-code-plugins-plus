# acme-widgets

> The fastest widget toolkit for the terminal.

![version](https://img.shields.io/badge/version-2.3.0-blue)

`acme-widgets` is a tiny demo CLI used as a golden fixture for the
content-consistency validator. It manages a local widget inventory.

See the [docs](docs/index.md), the [changelog](CHANGELOG.md), and the
[roadmap](planning/roadmap.md). The full walkthrough lives in `docs/usage.md`.

## Commands

| Command  | Description         |
| -------- | ------------------- |
| `create` | Create a new widget |
| `list`   | List all widgets    |

## Development

Run the test suite exactly as CI does:

```bash
npm run test:unit
```

Implementation lives in `src/cli.js`.

## License

This project is licensed under the MIT License.
