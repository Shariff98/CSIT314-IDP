# Design Match: Interior Design Platform (CSIT314 Group Project)

An online platform that matches renovation customers with interior designers. It implements all
60 user stories from the group's backlog across the six features in the project specification,
using a strict **boundary-control-entity (b-c-e)** design so the code matches the UML diagrams one to one.

| | |
| --- | --- |
| User stories implemented | **60 of 60** (one control class per story) |
| Detailed use cases (diagrammed) | **12**, two per member, marked ★ below |
| Unit tests | **224 passing**, 92% line coverage of control, entity and boundary |
| Test data | 202 accounts, 100 companies, 210 team members, 300 projects with photos, 2,600+ views, 260+ favourites |
| CI/CD | GitHub Actions runs tests + the data generator on every push; `main` deploys to Render |

## 1. Stack

| Layer | Choice |
| --- | --- |
| Backend | Python 3.12, Flask 3 (object-oriented: every b-c-e element is a class or a module of routes) |
| Frontend | Jinja HTML templates + Bootstrap 5 |
| Database | SQLite (one file, no server) |
| Tests | pytest + pytest-cov |
| CI/CD | GitHub Actions + Render |

The PHP comparison and the reasons for this stack are in `Design-Match-Tech-Stack-Guide.pdf`.

## 2. Run it

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python scripts/generate_data.py    # fresh platform.db + uploads/ with demo data (about 40 s)
python app.py                      # open http://127.0.0.1:5000
pytest -v                          # run all unit tests
pytest --cov=control --cov=entity --cov=boundary   # with a coverage report
```

`generate_data.py` deletes the old database each run, so the demo always starts from the same data.
Use `--size 20` for a quick, smaller set.

Demo logins (password for every generated account: `password123`):

| Role | Email | Lands on |
| --- | --- | --- |
| User Admin | admin@example.com | User accounts |
| Platform Management | manager@example.com | Platform dashboard |
| Interior Designer | designer0@example.com … designer99@example.com | My projects |
| Customer | customer0@example.com … customer99@example.com | Browse projects |

Visitors can also browse without logging in and can sign up as a customer at `/register`.

## 3. How b-c-e maps to the code

A request always flows one way: **user → Boundary → Control → Entity → database**.

| Layer | Folder | Rule |
| --- | --- | --- |
| Boundary | `boundary/` + `templates/` | Flask routes and HTML pages. Reads the form, calls **one controller**, shows the result. No business rules, no SQL. |
| Control | `control/` | **One class per user story.** Validates input and applies the acceptance criteria. Talks only to entities. |
| Entity | `entity/` | Data classes that load and save themselves. The only layer that touches SQLite (`db.py`) or uploaded files (`storage.py`). |

Controllers raise `ValueError` with a message the page can show (bad input) or `LookupError`
(not found, or someone else's data). Boundaries turn these into a red message or a 404.

Shared helpers inside the control layer: `validation.py` (email, numbers, dates, images),
`ownership.py` (a designer may only change their own projects) and `generate_report_controller.py`
(the parent class of the three report controllers).

```
design-match/
├── app.py                    # creates the Flask app and registers every boundary
├── boundary/                 # 8 route modules (pages)
│   ├── auth_boundary.py      #   LoginPage, RegisterPage, Log out
│   ├── account_boundary.py   #   User Admin: accounts and profiles
│   ├── company_boundary.py   #   Designer company info + public company page
│   ├── idp_boundary.py       #   Browse/search/filter, IDP detail, Create IDP
│   ├── portfolio_boundary.py #   Designer's own projects: edit, publish, status, photos, delete
│   ├── favourite_boundary.py #   Save / remove, My favourites
│   ├── analytics_boundary.py #   Designer interest tracking
│   └── platform_boundary.py  #   Categories, reports, dashboard
├── control/                  # 57 controller classes, one per story (US-07/18 share one)
├── entity/                   # UserAccount, UserProfile, Company, TeamMember, Category, IDP,
│                             # IDPPhoto, Favourite, ViewEvent, Notification, Report
├── templates/                # Bootstrap pages, one folder per actor
├── tests/                    # pytest unit tests
├── scripts/generate_data.py  # test data generator
└── .github/workflows/ci.yml  # CI/CD pipeline
```

## 4. User story → class map

★ = one of the 12 detailed use cases (class + sequence diagram). The controller file name is the class
name in snake case, e.g. `SearchMyIDPsController` is in `control/search_my_idps_controller.py`.

### Feature 1: user accounts and profiles

| Story | Boundary (page) | Control class · method | Entity | Tests |
| --- | --- | --- | --- | --- |
| US-01 Log out | Log out link `/logout` | `LogoutController.logout` | – | test_accounts_and_profiles |
| US-11 Update and suspend user profile | Edit profile `/admin/profiles/<id>/edit` | `UpdateUserProfileController.update_profile / suspend / reactivate` | UserProfile | test_accounts_and_profiles |
| ★ US-21 Create user account | Create account `/admin/accounts/new` | `CreateUserAccountController.create_account` | UserAccount, UserProfile | test_create_user_account_controller |
| US-22 View and search user accounts | Accounts `/admin/accounts` | `SearchUserAccountController.search` | UserAccount | test_accounts_and_profiles |
| US-23 Log in | Login `/login` | `LoginController.login` | UserAccount, UserProfile | test_accounts_and_profiles |
| US-31 View and search user profiles | Profiles `/admin/profiles` | `SearchUserProfileController.search` | UserProfile | test_accounts_and_profiles |
| US-41 Update user account | Edit account `/admin/accounts/<id>/edit` | `UpdateUserAccountController.update_account` | UserAccount | test_accounts_and_profiles |
| ★ US-42 Suspend and reactivate user account | Suspend / Reactivate buttons | `SuspendUserAccountController.suspend / reactivate` | UserAccount | test_suspend_user_account_controller |
| US-43 Customer self-registration | Sign up `/register` | `RegisterCustomerController.register` | UserAccount | test_accounts_and_profiles |
| US-51 Create user profile | Create profile `/admin/profiles/new` | `CreateUserProfileController.create_profile` | UserProfile | test_accounts_and_profiles |

### Feature 2: designer company information

| Story | Boundary (page) | Control class · method | Entity | Tests |
| --- | --- | --- | --- | --- |
| US-02 View company information | My company `/company` | `ViewCompanyInfoController.view` | Company | test_company |
| US-12 Certifications, awards, experience | Edit company `/company/edit` | `UpdateCredentialsController.update` | Company | test_company |
| US-13 Team members | Edit company | `ManageTeamMemberController.add / remove` | TeamMember, Company | test_company |
| US-14 Budget range and services | Edit company | `UpdateServicesController.update` | Company | test_company |
| US-15 Preview public company page | Preview `/company/preview` | `ViewCompanyPageController.view` | Company, IDP | test_company, test_boundary |
| US-24 Create company profile | `/company/new` | `CreateCompanyProfileController.create_company` | Company | test_company |
| US-25 Specialisations and service areas | Edit company | `UpdateSpecialisationsController.update` | Company | test_company |
| ★ US-32 Update company information | Edit company | `UpdateCompanyInfoController.update_company` | Company | test_update_company_info_controller |
| US-52 Logo and cover image | Edit company | `UploadCompanyImageController.upload` | Company (+ storage) | test_company |
| US-53 View designer company page | `/designers/<id>` | `ViewCompanyPageController.view` | Company, IDP, UserAccount | test_company |

### Feature 3: designer portfolio (IDPs)

| Story | Boundary (page) | Control class · method | Entity | Tests |
| --- | --- | --- | --- | --- |
| ★ US-03 Search and filter my IDPs | My projects `/my/idps` | `SearchMyIDPsController.search` | IDP | test_search_my_idps_controller |
| US-04 Update IDP | Edit project `/my/idps/<id>/edit` | `UpdateIDPController.update_idp` | IDP | test_portfolio |
| US-05 Delete IDP | Delete button | `DeleteIDPController.delete` | IDP | test_portfolio |
| US-06 Mark current or past | Status button | `MarkIDPStatusController.mark` | IDP | test_portfolio |
| US-16 View list of my IDPs | My projects | `ListMyIDPsController.list_idps` | IDP | test_portfolio |
| US-26 Assign category and style tags | Tags form on my project page | `AssignIDPTagsController.assign` | IDP, Category | test_portfolio |
| US-27 View my IDP details | `/my/idps/<id>` | `ViewMyIDPController.view` | IDP | test_portfolio |
| US-33 Draft, publish, unpublish | Publish button / Save as draft | `PublishIDPController.publish / unpublish` | IDP | test_portfolio |
| ★ US-54 Create IDP | New project `/idp/new` | `CreateIDPController.create_idp` | IDP, Category | test_create_idp_controller |
| US-55 Upload photos and set cover | Photo form on my project page | `UploadIDPPhotoController.upload / set_cover / delete_photo` | IDPPhoto (+ storage) | test_portfolio |

### Feature 4: customer search, view and favourites

| Story | Boundary (page) | Control class · method | Entity | Tests |
| --- | --- | --- | --- | --- |
| US-07 Browse published IDPs | Browse `/` | `BrowseIDPController.browse` | IDP | test_customer |
| US-08 Search and filter favourites | My favourites `/favourites?q=` | `SearchFavouritesController.search` | Favourite | test_customer |
| ★ US-17 Filter IDPs | Browse filters | `FilterIDPController.filter` | IDP | test_filter_idp_controller |
| US-18 Sort IDPs | Sort drop-down (`sort` argument of browse, search and filter) | `BrowseIDPController.browse(sort)` | IDP | test_customer, test_filter_idp_controller |
| ★ US-19 Save IDP to favourites | Save button | `SaveFavouriteController.save` | Favourite, IDP | test_save_favourite_controller |
| ★ US-28 Search IDPs by keyword | Search box | `SearchIDPController.search` | IDP | test_search_idp_controller |
| ★ US-34 View IDP details | `/idp/<id>` | `ViewIDPController.view` | IDP, ViewEvent | test_view_idp_controller |
| US-44 View favourites list | My favourites | `ViewFavouritesController.list_favourites` | Favourite | test_customer |
| US-45 Other projects by same designer | Detail page, bottom | `ViewDesignerProjectsController.other_projects` | IDP | test_customer |
| US-56 Remove from favourites | Remove button | `RemoveFavouriteController.remove` | Favourite | test_customer |

### Feature 5: interest tracking (views and shortlists)

| Story | Boundary (page) | Control class · method | Entity | Tests |
| --- | --- | --- | --- | --- |
| US-09 Rank IDPs | `/analytics/rank` | `RankIDPsController.rank` | IDP | test_interest_tracking |
| US-29 View IDP view count | `/analytics/views` | `ViewIDPViewCountController.view_counts` | IDP | test_interest_tracking |
| US-35 Views and shortlists by date range | `/analytics/trend` | `ViewInterestByDateRangeController.trend` | IDP (view_event, favourite) | test_interest_tracking |
| US-36 Filter analytics | `/analytics/segment` | `FilterAnalyticsController.filter` | IDP | test_interest_tracking |
| US-37 Count repeat views once per session | (inside IDP detail) | `ViewIDPController.view(session_key)` | ViewEvent | test_view_idp_controller |
| ★ US-46 View IDP shortlist count | `/analytics/shortlists` | `ViewShortlistCountController.shortlist_counts` | IDP, Favourite | test_view_shortlist_count_controller |
| US-47 Export statistics as CSV | `/analytics/export.csv` | `ExportInterestCSVController.export` | IDP | test_interest_tracking |
| US-48 Milestone notifications | `/analytics/notifications` + badge | `NotifyMilestoneController.check / list_notifications` | Notification | test_interest_tracking |
| US-57 Portfolio analytics dashboard | `/analytics/` | `PortfolioDashboardController.summary` | IDP | test_interest_tracking |
| US-58 Compare IDP performance | `/analytics/compare` | `CompareIDPsController.compare` | IDP | test_interest_tracking |

### Feature 6: platform management

| Story | Boundary (page) | Control class · method | Entity | Tests |
| --- | --- | --- | --- | --- |
| ★ US-10 Generate weekly report | `/platform/reports/weekly` | `GenerateWeeklyReportController.generate` | Report | test_generate_weekly_report_controller |
| US-20 Top categories and IDPs | `/platform/demand` | `ViewTopCategoriesController.view` | Report | test_platform |
| US-30 Generate monthly report | `/platform/reports/monthly` | `GenerateMonthlyReportController.generate` | Report | test_platform |
| US-38 Update category | `/platform/categories/<id>/edit` | `UpdateCategoryController.update_category` | Category | test_platform |
| US-39 Generate daily report | `/platform/reports/daily` | `GenerateDailyReportController.generate` | Report | test_platform |
| US-40 Export reports as PDF or CSV | Export buttons | `ExportReportController.export` | Report | test_platform |
| US-49 Create IDP category | `/platform/categories/new` | `CreateCategoryController.create_category` | Category | test_platform |
| US-50 Platform metrics dashboard | `/platform/` | `PlatformDashboardController.metrics` | Report | test_platform |
| ★ US-59 View and search categories | `/platform/categories` | `SearchCategoryController.search` | Category | test_search_category_controller |
| US-60 Suspend or delete category, reassign IDPs | Suspend / Delete with "Move IDPs to" | `SuspendCategoryController.suspend / delete` | Category | test_platform |

## 5. Sequence diagrams for the 12 detailed use cases

Draw each diagram with exactly these class and method names, and the design will match the code.
Every use case has the precondition "user is logged in with the right role" (no «include» Log in).

| ★ Use case | Boundary → Control | Control → Entity |
| --- | --- | --- |
| US-03 Search and filter my IDPs | `MyIDPsPage → SearchMyIDPsController.search(designer_id, keyword, status, category, date_from, date_to)` | `→ IDP.list_for_designer(...)` |
| US-10 Generate weekly report | `ReportPage → GenerateWeeklyReportController.generate(ref_date)` | `→ date_range(ref)` (self), `→ Report.build("Weekly", start, end)` twice (this week and last week) |
| US-17 Filter IDPs | `SearchIDPPage → FilterIDPController.filter(keyword, category, style, min_budget, max_budget, property_type, location, sort)` | `→ IDP.filter(...)` |
| US-19 Save IDP to favourites | `IDPDetailPage → SaveFavouriteController.save(customer_id, idp_id)` | `→ IDP.find_by_id`, `→ Favourite.add`, `→ NotifyMilestoneController.check(idp)` |
| US-21 Create user account | `CreateAccountPage → CreateUserAccountController.create_account(name, email, password, role)` | `→ UserProfile.find_by_name`, `→ UserAccount.find_by_email`, `→ UserAccount.create` |
| US-28 Search IDPs by keyword | `SearchIDPPage → SearchIDPController.search(keyword, sort)` | `→ IDP.search(keyword, sort)` |
| US-32 Update company information | `EditCompanyPage → UpdateCompanyInfoController.update_company(designer_id, ...)` | `→ Company.find_by_designer`, `→ Company.registration_taken`, `→ company.save(...)` |
| US-34 View IDP details | `IDPDetailPage → ViewIDPController.view(idp_id, viewer_id, session_key)` | `→ IDP.find_by_id`, `→ idp.seen_in_session`, `→ idp.record_view` (→ `ViewEvent.record`) |
| US-42 Suspend / reactivate account | `AccountsPage → SuspendUserAccountController.suspend(admin_id, account_id)` | `→ UserAccount.find_by_id`, `→ account.suspend()` |
| US-46 View IDP shortlist count | `ShortlistsPage → ViewShortlistCountController.shortlist_counts(designer_id)` | `→ IDP.list_for_designer`, `→ idp.shortlist_count()` for each |
| US-54 Create IDP | `CreateIDPPage → CreateIDPController.create_idp(designer_id, title, ...)` | `→ Category.find_by_name` (check), `→ IDP.create(...)` |
| US-59 View and search categories | `CategoriesPage → SearchCategoryController.search(keyword, status)` | `→ Category.search`, `→ category.idp_count()` for each |

Example in full, US-54:

```
Designer -> CreateIDPPage : submit form
CreateIDPPage -> CreateIDPController : create_idp(designer_id, title, description, category, budget, ...)
CreateIDPController -> CreateIDPController : validate input (required fields, budget > 0, tags <= 5)
CreateIDPController -> Category : find_by_name(category)
Category --> CreateIDPController : active category
CreateIDPController -> IDP : create(...)
IDP --> CreateIDPController : new IDP
CreateIDPController --> CreateIDPPage : new IDP
CreateIDPPage --> Designer : show the project page
```

## 6. Data model (SQLite)

| Table | Main columns | Notes |
| --- | --- | --- |
| user_profile | name, description, status | The 4 built-in roles are created automatically |
| user_account | name, email, password_hash, role, status, created_at | Passwords are hashed; role = a profile name |
| company | designer_id, name, registration_no, address, phone, email, description, specialisations, service_areas, certifications, awards, years_experience, budget_min, budget_max, services, logo_file, cover_file | One per designer |
| team_member | company_id, name, position | |
| category | name, description, status, created_at | 5 defaults created automatically |
| idp | designer_id, title, description, category, budget, style_tags, property_type, location, completion_date, status (Current/Past), published (draft = 0), views, created_at | |
| idp_photo | idp_id, filename, is_cover | Files stored in `uploads/` |
| favourite | customer_id, idp_id, saved_at | A save = one shortlist |
| view_event | idp_id, customer_id, session_key, viewed_at | One row per counted view, used for trends and reports |
| notification | designer_id, idp_id, message, is_read | View and shortlist milestones |

Deleting a project also deletes its photos, favourites and view history (`ON DELETE CASCADE`).

## 7. Test-driven development

- Each acceptance criterion is one test. The 12 detailed use cases each have their own test file
  (`tests/test_<controller>.py`); the other stories are grouped by feature (`test_accounts_and_profiles.py`,
  `test_company.py`, `test_portfolio.py`, `test_customer.py`, `test_interest_tracking.py`, `test_platform.py`).
- `test_boundary.py` drives the real pages as each of the four roles. `test_generate_data.py` checks the generator.
- Every test gets a fresh, empty database and upload folder (`tests/conftest.py`).

For the report: for at least one story per member, commit the failing test first (red), then the code (green),
and screenshot both runs. The commit history is the TDD evidence.

## 8. CI/CD

`.github/workflows/ci.yml` runs on every push and pull request:

1. installs the requirements,
2. runs all tests with a coverage report,
3. runs `generate_data.py --size 20` to prove the demo data still builds,
4. on `main` only, when green, calls the Render deploy hook.

Set up the deploy once:

1. On [render.com](https://render.com) create a **Web Service** from the repo.
   Build command: `pip install -r requirements.txt`.
   Start command: `python scripts/generate_data.py && gunicorn "app:create_app()"`
   (Render's free disk resets on each deploy, so the demo data is rebuilt at start).
2. Copy Render's **Deploy Hook** URL into GitHub: Settings → Secrets and variables → Actions → `RENDER_DEPLOY_HOOK`.
3. Set an environment variable `SECRET_KEY` on Render to a long random string.
4. For the report, screenshot one feature going from pull request → green CI → deployed.

## 9. Test data

`python scripts/generate_data.py` creates, with a fixed random seed:

| Data type | Records |
| --- | --- |
| User accounts | 202 (1 admin, 1 manager, 100 designers, 100 customers; 5 customers suspended) |
| Companies | 100, each with specialisations, services, budget range |
| Team members | about 210 |
| Projects (IDPs) | 300 (about 10% drafts, a mix of current and past), spread over 6 months |
| Photos | 300 cover images (generated PNGs) |
| Views | about 2,650 with timestamps |
| Favourites | about 260 |
| Notifications | about 125 milestone notifications |
| Categories | 20 |
| User profiles | 5 (the 4 roles + 1 example custom profile) |

Categories and profiles are naturally small lists; every data type that grows with use has 100+ records.

## 10. Ethics and security built into the code

- Passwords are stored only as salted hashes (Werkzeug `generate_password_hash`).
- Suspending an account or a profile blocks login but keeps the data (no silent deletion).
- Designers can only see and change their own drafts, projects, photos and statistics (`control/ownership.py`).
  Someone else's project returns "not found", so drafts can't be discovered.
- Customers' favourites are private; designers see only counts, never who saved a project.
- View counts ignore the owner and repeat views in one session, so statistics aren't inflated (US-37).
- Uploads are limited to image types and 5 MB, and stored under random file names.

Known limits, worth a line in the report: forms have no CSRF tokens (add Flask-WTF before real use),
and custom user profiles (US-51) can be created and assigned but don't unlock extra pages; only the
four built-in roles have pages.

## 11. Suggested ownership (2 detailed use cases per member)

| Member | ★ Use cases | Also owns (same feature area) |
| --- | --- | --- |
| 1 | US-03, US-10 | US-01, 02, 04, 05, 06, 07, 08, 09 |
| 2 | US-17, US-19 | US-11, 12, 13, 14, 15, 16, 18, 20 |
| 3 | US-21, US-28 | US-22, 23, 24, 25, 26, 27, 29, 30 |
| 4 | US-32, US-34 | US-31, 33, 35, 36, 37, 38, 39, 40 |
| 5 | US-42, US-46 | US-41, 43, 44, 45, 47, 48, 49, 50 |
| 6 | US-54, US-59 | US-51, 52, 53, 55, 56, 57, 58, 60 |

This follows the "Assigned To" column in the group's user story spreadsheet.
