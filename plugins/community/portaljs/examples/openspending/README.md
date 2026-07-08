# A data catalog with data on GitHub

This example showcases a simple data catalog that get its data from a list of GitHub repos that serve as datasets.

A `datasets.json` file is used to specify which datasets are going to be part of the data catalog.

The application contains an index page, which lists all the datasets specified in the `datasets.json` file, and users can see more information about each dataset, such as the list of data files in it and the README, by clicking the "info" button on the list.

You can read more about it on the [Data catalog with data on GitHub](https://portaljs.com/docs/examples/github-backed-catalog) blog post.

## Demo

https://example.portaljs.org/

## Deploy your own

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https%3A%2F%2Fgithub.com%2Fdatopian%2Fportaljs%2Ftree%2Fmain%2Fexamples%2Fgithub-backed-catalog)

By clicking on this button, you will be redirected to a page which will allow you to clone the content into your own GitHub/GitLab/Bitbucket account and automatically deploy everything.

## How to use

### Install

Execute `create-next-app` to bootstrap the example:

```
npx create-next-app <app-name> --example https://github.com/datopian/portaljs/tree/main/examples/github-backed-catalog
cd <app-name>
```

### Set environment variables

This project uses the GitHub API, which for anonymous users will cap at 50 requests per hour, so you might want to get a [Personal Access Token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token) and add it to a `.env` file inside the folder like so

```
GITHUB_PAT=<github token>
```

### Change datasets

You can change the datasets that will be displayed in the data catalog by editing the file `datasets.json`. Some examples can be found inside [this repo](https://github.com/datasets).

### Run in development mode

Run the app using:

```
npm run dev
```

Open http://localhost:3000 from your browser. You should see something similar to this:

![](https://i.imgur.com/jAljJ9C.png)

If click on the `info` button for a dataset you will see a page similar to this:

![](https://i.imgur.com/AoJd4O0.png)

## Notes

### Structure of `datasets.json`

The `datasets.json` file is simply a list of datasets, below you can see a minimal example of a dataset:

```json
{
  "owner": "fivethirtyeight",
  "repo": "data",
  "branch": "master",
  "files": ["nba-raptor/historical_RAPTOR_by_player.csv", "nba-raptor/historical_RAPTOR_by_team.csv"],
  "readme": "nba-raptor/README.md"
}
```

It has:

- A `owner` which is going to be the github repo owner
- A `repo` which is going to be the github repo name
- A `branch` which is going to be the branch to which we need to get the files and the readme
- A list of `files` which is going to be a list of paths with files that you want to show to the world
- A `readme` which is going to be the path to your data description, it can also be a subpath eg: `example/README.md`

You can also add:

- A `description` which is useful if you have more than one dataset for each repo, if not provided we are just going to use the repo description
- A `Name` which is useful if you want to give your dataset a nice name, if not provided we are going to use the junction of the `owner` the `repo` + the path of the README, in the exaple above it will be `fivethirtyeight/data/nba-raptor`

### Extra commands

You can also build the project for production with:

```
npm run build
```

And run the production build with:

```
npm run start
```

