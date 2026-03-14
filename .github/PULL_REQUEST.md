## Summary                                                                             
                                                                                       
  Implement Google OAuth 2.0 Authorization Code Flow and refactor the Trello client      
  constructor to accept credentials as parameters instead of reading from environment    
  variables.                                                                             
                                                                                         
  ## Changes

  - Refactored `DefaultIssueTrackerClient` constructor to accept `api_key` and `token` as
   parameters
  - Updated DI factory registration to use a lambda that reads env vars
  - Added `oauth.py` module with Google OAuth 2.0 helpers: `build_authorization_url`,
  `exchange_code_for_token`, `refresh_access_token`
  - Updated all existing unit tests for new constructor signature
  - Added comprehensive unit tests for OAuth helper functions

  ## Files Modified

  - `components/issue_tracker_client_impl/src/issue_tracker_client_impl/client.py` —
  constructor now takes `api_key` and `token` params
  - `components/issue_tracker_client_impl/src/issue_tracker_client_impl/__init__.py` — DI
   registration uses lambda with env vars
  - `components/issue_tracker_client_impl/src/issue_tracker_client_impl/oauth.py` —
  **new** Google OAuth 2.0 helper functions
  - `components/issue_tracker_client_impl/tests/test_impl.py` — updated fixtures and init
   tests
  - `components/issue_tracker_client_impl/tests/test_oauth.py` — **new** OAuth unit tests

  ## Testing

  - [ ] All unit tests pass (`pytest components/ -v`)
  - [ ] Ruff passes (`ruff check .`)
  - [ ] MyPy passes (`mypy -p issue_tracker_client_api -p issue_tracker_client_impl
  --explicit-package-bases`)
  - [ ] Coverage meets 85% threshold

  ## Notes for Reviewers

  - OAuth provider is Google (Internal NYU users only)
  - The FastAPI service (Task 2) should import from `oauth.py` for auth endpoints
  - The FastAPI service should construct the client per-request:
  `DefaultIssueTrackerClient(api_key=os.environ["TRELLO_API_KEY"], token=session_token)`
  - New env vars required: `OAUTH_CLIENT_ID`, `OAUTH_CLIENT_SECRET`, `REDIRECT_URI` —
  shared privately, never committed
  - Once a production URL is available, it must be added as a redirect URI in the Google
  Cloud Console