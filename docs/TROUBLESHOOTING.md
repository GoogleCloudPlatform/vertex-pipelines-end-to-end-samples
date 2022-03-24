# Troubleshooting

List of common issues during project setup:

```bash
$ make run pipeline=<training|prediction>`

google.auth.exceptions.DefaultCredentialsError: Could not automatically determine credentials. 
Please set GOOGLE_APPLICATION_CREDENTIALS or explicitly create credentials and re-run the application.
```

**Solution:** `gcloud auth application-default login`

```bash
$ make run pipeline=<training|prediction>

google.api_core.exceptions.InvalidArgument: 400 You do not have permission to act as service_account: 
<...>@<...>.iam.gserviceaccount.com. (or it may not exist).
```

**Solution:** Ensure the service account mentioned in `.env.sh` (`VERTEX_SA_EMAIL`) 
exists and you have permission to act as the service account.

```bash
$ make unit-tests

FAILED tests/kfp_components/xgboost/train/test_train.py::test_xgboost_train - xgboost.core.XGBoostError: XGBoost Library (libxgboost.dylib) could not be loaded.
```

**Solution:** if you are using macOS, try to also install XGBoost using Homebrew: `brew install xgboost`
