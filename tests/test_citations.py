from adaptive_router.catalog import entries


def test_sdk_citations_use_published_package_paths_and_method_anchors():
    links = {symbol: url for symbol, _, url, *_ in entries()}
    root = "https://learn.microsoft.com/en-us/python/api/"
    assert links["BlobClient.download_blob"] == (
        root + "azure-storage-blob/azure.storage.blob.blobclient?view=azure-python"
        "#azure-storage-blob-blobclient-download-blob"
    )
    assert links["DefaultAzureCredential"] == (
        root + "azure-identity/azure.identity.defaultazurecredential?view=azure-python"
    )
