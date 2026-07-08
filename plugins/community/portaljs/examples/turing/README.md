This demo d ata portal is designed for https://hatespeechdata.com. It catalogs datasets annotated for hate speech, online abuse, and offensive language which are useful for training a natural language processing system to detect this online abuse.

The site is built on top of [PortalJS](https://portaljs.com/). It catalogs datasets and lists of offensive keywords. It also includes static pages. All of these are stored as markdown files inside the `content` folder.

- .md files inside `content/datasets/` will appear on the dataset list section of the homepage and be searchable as well as having a individual page in `datasets/<file name>`
- .md files inside `content/keywords/` will appear on the list of offensive keywords section of the homepage as well as having a individual page in `keywords/<file name>`
- .md files inside `content/` will be converted to static pages in the url `/<file name>` eg: `content/about.md` becomes `/about`

This is also a Next.JS project so you can use the following steps to run the website locally.

## Getting started

To get started first clone this repo in your local machine like so:

```bash
npx create-next-app turing --example https://github.com/datopian/portaljs/tree/main/examples/turing
cd turing
```

Then install the npm dependencies:

```bash
npm install
```

Next, run this command, its related to [markdowndb](https://github.com/datopian/markdowndb):
```bash
npm run mddb
```

Next, run the development server:

```bash
npm run dev
```

Finally, open [http://localhost:3000](http://localhost:3000) in your browser to view the website.
