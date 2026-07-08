This example creates a portal/showcase for a single dataset. The dataset should be a [Frictionless dataset (data package)][fd] i.e. there should be a `datapackage.json`.

[fd]: https://specs.frictionlessdata.io/data-package/

## How to use

```bash
npx create-next-app -e https://github.com/datopian/portal.js/tree/main/examples/dataset-frictionless
# choose a name for your portal when prompted e.g. your-portal or go with default my-app

# then run it
cd your-portal
yarn #install packages
yarn dev #start app in dev mode
```

You should see the demo portal running with the example dataset provided:

<img src="./assets/demo.gif" />

### Use your own dataset

You can try it out with other [Frictionless datasets](https://datahub.io/search).

In the directory of your portal do:

```bash
export PORTAL_DATASET_PATH=/path/to/my/dataset
```

Then restart the dev server:

```
yarn dev
```

Check the portal page and it should have updated e.g. like:

![](https://i.imgur.com/KSEtNF1.png)
