# Matching LIS to TecDoc

For Design Doc, see [here](https://teams.microsoft.com/_?culture=en-us&country=WW&lm=deeplink&lmsrc=homePageWeb&cmpid=WebSignIn#/docx/viewer/teamsSdk/https:~2F~2Folyslager.sharepoint.com~2Fsites~2FOlyslagerenLennartDamenvanBDR~2FGedeelde%20documenten~2FGeneral~2FDesign%20doc.docx?threadId=19:Bx4MdOlFK4pmpv661ltxZSCYt8J_siLZVkeTX1WRhFA1@thread.tacv2&fileId=e540b140-2d44-4282-b099-b49d09e51feb&ctx=openFilePreview&viewerAction=view).

## Installation
To run this project, you need [Docker Desktop](https://www.docker.com/get-started/). After installation, start Docker
and run the following command in the working directory of this project:

```docker pull mcr.microsoft.com/mssql/server:2019-latest```

This will build the Docker image for running SQL Server.

## Usage
To start the container, run:

```docker-compose up```

To enter the container, run:

```./scripts/enter_container.sh```

You are now logged in as the root user of MySQL, and  should see a `mysql>` prefix at the start of your command line.
To check that everything works currectly, run the MySQL command:

```show databases;```

Next, we will import the LIS extracts into our MySQL database. For that, run:

```./scripts/import_extracts.sh```

