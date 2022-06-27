# Matching LIS and TecDoc

For project documentation Doc, see [here](https://olyslager.sharepoint.com/:p:/r/sites/OlyslagerenLennartDamenvanBDR/Gedeelde%20documenten/General/Oplevering%2027_07_2022.pptx?d=wd5f8d02f8467435ab0fc403a5a3fc03f&csf=1&web=1&e=hfwuKI).

## Installation
The easiest way to run this project is to use [Docker Desktop](https://www.docker.com/get-started/). After installation, start Docker
and run the following command in the working directory of this project:

```docker-compose build```

This will build the Docker image for running the matching process.

If you want to test, validate, or modify the algorithm, I recommend to install the package on your host system:
- [download miniconda](https://docs.conda.io/en/latest/miniconda.html)
- install python 3.7.5: `conda create --name my-env-name python=3.7.5`
- activate the environment: `conda activate my-env-name`. You should then see `(my-env-name)`
appear on your command line.
- install the required packages: `pip install .`. Alternatively, if you plan on modifying the code, install
the package in "editable" mode: `pip install -e .["dev"]`

## Usage
### Docker
First, make sure to add two files to the `./data/raw` folder:
- `lis.xlsx`, the LIS records
- `tecdoc.xlsx`, the TecDoc records.

To start the matching process using a docker container, run: `docker-compose up`. The default command for the container
is `olyslager match`. This command is coupled to the python-entrypoint defined in `./oly_matching/cli.py`,
under the function `match`.

The container uses two volumes: `./data` and `./oly_matching` (the source code). If you edit the source code,
the container's behaviour will change accordingly.

The matching algorithm produces several results, which are stored as output files under `./data/output`:
- matches_per_lis_id.xlsx: for each LIS type ID, state which N-types correspond to it (together with extra info)
- links_with_original_data.xlsx: for every link between LIS and TecDoc, state what was the
                                 original information in LIS and TecDoc (used to validate matches by hand)
- metrics: overall overview of matching performance
- results_per_model.xlsx: overview of performance per model (useful for identifying algorithm improvements)

The docker container runs the "exact" matching algorithm by default. There are two other matching methods:
'cut_strings' and 'fuzzy'. In case you want to run 'cut_strings', enter change the 'entrypoint' in the
docker-compose.yml like so:
`entrypoint: ["olyslager", "match", "--matching-method=cut_strings"]`
Then, run `docker-compose up` same like before.

### Host OS
If you have installed the package on your host system directly, you can run: `olyslager match`
directly on the command line.  The `olyslager match` command takes four optional arguments:
- `--lis-path`: path to LIS excel file (default: ./data/raw/lis.xlsx)
- `--tecdoc-path`: path to TecDoc excel file (default: ./data/raw/tecdoc.xlsx)
- `--output-folder`: where to store the output files (this folder must already exist. default: ./data/output)
-  `"--matching-method"`: choose from: exact (default), cut_strings, fuzzy

For instance, you could enter:
`olyslager match --lis-path="/path/to/my_folder/lis.xlsx"`
