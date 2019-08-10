# How to setup server:
#### In debian based linux (ex. ubuntu):
```bash
git clone https://github.com/idomoz/wordcountdeluxe
cd wordcountdeluxe
```
* Run the following and replace `<YOUR_SECRET_KEY>` with your recaptcha secret key:
* You can also use this working secret key: `6LcWBrIUAAAAAGViwcVkqplRhhpis5TW21FCEoBC`
* (The corresponding site key for frontend integration is: `6LcWBrIUAAAAAPMJ-ZFUsmgkw4yMx0TterNZYlnG`)

    ```bash
    sed -i "s/<recaptcha_secret_key>/<YOUR_SECRET_KEY>/g" app/main.py
    ```
* Run the following and replace `<YOUR_SITE_HOSTNAME>` with your site's hostname:
* (The hostname that corresponds with the above key is `testrecaptcha.tk`)
    ```bash
    sed -i "s/<example.com>/<YOUR_SITE_HOSTNAME>/g" app/main.py
    ```
* Run the following and replace `<YOUR_JWT_SECRET>` with your jwt secret:
    ```bash
    sed -i "s/<jwt_secret>/<YOUR_JWT_SECRET>/g" app/main.py
    ```

```bash
chmod +x setup.sh
./setup.sh
```
* The server will listen on port 80

## API
* All endpoints expect json data.
### /register  [POST]:
* Receives:
```json
{
  "email": "<email>",
  "password": "<password>",
  "token": "<recaptcha_token>"
}
```
* Registers the email and returns jwt on success

### /login  [POST]:
* Receives:
```json
{
  "email": "<email>",
  "password": "<password>",
  "token": "<recaptcha_token>"
}
```
* Returns jwt on success

### /word_count  [POST]:
* Receives the following json and `Authorization` header with jwt:
```json
{
  "url": "<url>",
  "words": ["search_word_1", "search_word_2", "...", "search_word_n"]
}
```
* Returns json with the amount every word appears in the page on the given url. ex.:
```json
{
  "search_word_1": 2,
  "search_word_2": 0,
  "search_word_n": 5
}
```
