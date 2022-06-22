# Matching LIS and TecDoc

For project documentation Doc, see [here](https://olyslager.sharepoint.com/:p:/r/sites/OlyslagerenLennartDamenvanBDR/Gedeelde%20documenten/General/Progress%20slides.pptx?d=wdc8b4767401a4737b1de5b492a2546fa&csf=1&web=1&e=X4kx76).
## Installation
The easiest way to run this project is to use [Docker Desktop](https://www.docker.com/get-started/). After installation, start Docker
and run the following command in the working directory of this project:

```docker-compose build```

This will build the Docker image for running the matching process.

If you prefer to install on your host system, I recommend to:
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
- matches_per_lis_id.csv: for each LIS type ID, state which N-types correspond to it (together with extra info)
- metrics: overall overview of matching performance
- results_per_model.csv: overview of performance per model (useful for identifying algorithm improvements)
- lis_records_with_match.csv: detailed records from LIS, left-joined with corresponding TecDoc records

### Host OS
If you have installed the package on your host system directly, you can run: `olyslager match`
directly on the command line.  The `olyslager match` command takes three optional arguments:
- `--lis-path`: path to LIS excel file
- `--tecdoc-path`: path to TecDoc excel file
- `--output-folder`: where to store the output files (this folder must already exist)

For instance, you could enter:
`olyslager match --lis-path="/path/to/my_folder/lis.xlsx"`
