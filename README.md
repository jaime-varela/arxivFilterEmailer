# arxivFilterEmailer

A simple arxiv filter and emailer.  I run this on a cron job daily for getting filterd email results from the arxiv rss feed.


![example](doc/filteredEmail.png "Filtered email")

In order to use one needs to create a 'config.py' file and create a few dictionaries.  See 'sampleConfig.py' to see the necessary dictionary information.

If 'IMPORT_DROPBOXFILE' is true the code will use the config files dropbox token to download 'arxivMeta.json' otherwise it will use the local copy (the arxivMeta file needs to be in the arxiv root directory).

The 'arxivMeta.json' contains a json file with and array of objects of the form:

```json
{
    "arxivSite": "cs",
    "authors": [
        "Ian Goodfellow",
        "Daniel A. Roberts"
    ],
    "words": [
        "quantum computing",
        "RTOS"
    ]
}
```

Here 'arxivSite' is the arxive site (cs or hep-th for example), 'authors' is an arxiv author you want filtered (copy and paste the author name from arxiv, needs to be full name), and 'words' are a set of words you want filtered from the abstracts.

Running this around mid-day should run the filter and send an email.  It's best to set up a cron job as needed, see 'cronText.txt' as an example for a daily emailer.