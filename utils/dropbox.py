# set up dropbox
import dropbox


def download_dropbox_file(dropbox_path="", target_file="",token=""):
    dbx = dropbox.Dropbox(token)
    with open(target_file, "wb") as f:
        metadata, res = dbx.files_download(path=dropbox_path)
        f.write(res.content)
