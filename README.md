# Matching LIS and TecDoc

For Design Doc, see [here](https://teams.microsoft.com/_?culture=en-us&country=WW&lm=deeplink&lmsrc=homePageWeb&cmpid=WebSignIn#/docx/viewer/teamsSdk/https:~2F~2Folyslager.sharepoint.com~2Fsites~2FOlyslagerenLennartDamenvanBDR~2FGedeelde%20documenten~2FGeneral~2FDesign%20doc.docx?threadId=19:Bx4MdOlFK4pmpv661ltxZSCYt8J_siLZVkeTX1WRhFA1@thread.tacv2&fileId=e540b140-2d44-4282-b099-b49d09e51feb&ctx=openFilePreview&viewerAction=view).

## Installation
To run this project, you need [Docker Desktop](https://www.docker.com/get-started/). After installation, start Docker
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
First, make sure to add two files to the `./data/raw` folder:
- `lis.xlsx`, the LIS records
- `tecdoc.xlsc`, the TecDoc records.

To start the matching process using a docker container, run: `docker-compose up`.

If you have installed the package on your host system directly, you can run: `olyslager match`
directly on the command line. The `olyslager match` command takes three optional arguments:
- `--lis-path`: path to LIS excel file
- `--tecdoc-path`: path to TecDoc excel file
- `--output-folder`: where to store the output files (this folder must already exist)

For instance, you could enter:
`olyslager match --lis-path="/path/to/my_folder/lis.xlsx"`

Regardless of the installation method, the output files will appear in `./data/output`:
- lis_ids_with_n_types.csv: for each LIS type ID, state which N-types correspond to it
- unmatched_lis_ids.csv: list of LIS ID's for which the algorithm could not find a match at all
- lis_records_with_match.csv: detailed records from LIS, left-joined with corresponding TecDoc records

The logs contain additional information. The most important information is the percentage of LIS records
that received one or more TecDoc ID's.