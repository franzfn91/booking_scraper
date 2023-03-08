# booking-scraper

Simple scraper for Booking searches with notifications for new stays.

## Usage

> For the full usage check the `booking-scraper --help` command

Create a configuration file using

``` bash
booking-scraper create-config <path/to/config.json>
```

The example configuration file will look like this:

```json

{
  "filter": {
    "exclude_patterns": []
  },
  "notifications": {
    "pushover": {
        "token": "<your-app-api-token>",
        "user": "<your-user-api-token>",
        "device": []
    }
  },
  "searches": [
    {
      "name": "Hotels in Rovinj",
      "url": "https://www.booking....",
      "recursive": true
    }
  ]
}

```

See [Configuration](#configuration) for details on all configuration options.

* Configure one or more searches in the `searches` section of the configuration, see [Searches](#searches) for
  more details
* Configure notifications in the `notifications` section of the configuration, see [Notifications](#notifications)
  for details on notification configuration
* (Optional) Configure filters in the `filter` section of the configuration, see [Filter](#filter) for more details

Run the following command to initialize the data store without sending any notifications:

``` bash
booking-scraper run --no-notifications path/to/config.json
```

Afterwards, run

```bash
booking-scraper run path/to/config.json
```

to receive notifications according to your `notifications` configuration.

## Development

Follow the steps below to set up a development environment for this project.

1. Clone this repository

   ``` bash
   git clone git@github.com:flfranz91/booking-scraper.git
   ```

2. Change into the repository

   ``` bash
   cd booking-scraper
   ```

3. Create a virtual environment

   ``` bash
   python3 -m venv .venv && . .venv/bin/activate
   ```

4. Install the package as an editable installation along with its dev dependencies

   ``` bash
   pip3 install -e .[dev]
   ```

5. (Optional) Install pre-commit environment

   ``` bash
   $ pre-commit
   [INFO] Installing environment for https://github.com/pre-commit/pre-commit-hooks.
   [INFO] Once installed this environment will be reused.
   [INFO] This may take a few minutes...
   [INFO] Installing environment for https://github.com/psf/black.
   [INFO] Once installed this environment will be reused.
   [INFO] This may take a few minutes...
   Check Yaml...........................................(no files to check)Skipped
   Fix End of Files.....................................(no files to check)Skipped
   Trim Trailing Whitespace.............................(no files to check)Skipped
   black................................................(no files to check)Skipped
   ```

## Configuration

### Searches

Searches can be configured in the `searches` array of the configuration file. Each of the searches can be configured
with the following parameters.

| Name | Description |
| ---- | ----------- |
| `name` | Name of the search, use a descriptive one (required) |
| `url` | URL of the first page of your search (required) |

### Filter

Filters can be configured in the `filter` section of the configuration file to exclude specific ads from your scrape
results on the client side. The following settings can be configured.

| Name | Description |
| ---- | ----------- |
| `exclude_patterns` | Case-insensitive regular expression patterns used to exclude ads (optional) |

### Notifications

Notifications can be configured in the `notifications` section of the configuration file.

#### Push notifications using Pushover

`booking-scraper` supports push notifications to your devices using [Pushover](https://pushover.net/).
For further information on the service check their terms and conditions.

The implementation for _Pushover_ notifications will send a single notification per search, if new ads are discovered.

To configure _Pushover_ for notifications from the scraper, first register at the service and create an application
(e.g. `booking-scraper`). To use the service in `booking-scraper`, add the `pushover` object to the `notifications` object in your
configuration file and fill the API tokens. Selection of the devices which will receive the notifications, is supported using the `device` array.

| Name | Description |
| ----- | ---------- |
| `token` | API token of the Pushover app (required) |
| `user` | API token of the Pushover user (required) |
| `device` | List of device names to send the notifications to <br/>(optional, defaults to all devices) |
