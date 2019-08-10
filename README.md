# How to setup server:
#### In debian based linux (ex. ubuntu):
```
git clone https://github.com/idomoz/wordcountdeluxe
cd wordcountdeluxe
```
* Run the following and replace `<YOUR_SITE_SECRET>` with your recaptcha site secret:
    ```
    sed -i "s/<recaptcha_site_secret>/<YOUR_SITE_SECRET>/g" app/main.py
    ```
* Run the following and replace `<YOUR_SITE_HOSTNAME>` with your site's hostname:
    ```
    sed -i "s/<example.com>/<YOUR_SITE_HOSTNAME>/g" app/main.py
    ```
* Run the following and replace `<YOUR_JWT_SECRET>` with your jwt secret:
    ```
    sed -i "s/<jwt_secret>/<YOUR_JWT_SECRET>/g" app/main.py
    ```

```
chmod +x setup.sh
./setup.sh
```
* The server will listen on port 80
