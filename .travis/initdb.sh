#!/bin/bash

# Adapted from https://github.com/PyMySQL/PyMySQL/blob/master/.travis/initializedb.sh

set -ex

docker pull ${DB}
docker run -it --name=mysqld -d -e MYSQL_ALLOW_EMPTY_PASSWORD=yes -p 3306:3306 ${DB}

mysql() {
    docker exec mysqld mysql "${@}"
}
while :
do
    sleep 3
    mysql --protocol=tcp -e 'select version()' && break
done
docker logs mysqld

if [ $DB == 'mysql:8.0' ]; then
    WITH_PLUGIN='with mysql_native_password'
    mysql -e 'SET GLOBAL local_infile=on'
    docker cp mysqld:/var/lib/mysql/public_key.pem "${HOME}"
    docker cp mysqld:/var/lib/mysql/ca.pem "${HOME}"
    docker cp mysqld:/var/lib/mysql/server-cert.pem "${HOME}"
    docker cp mysqld:/var/lib/mysql/client-key.pem "${HOME}"
    docker cp mysqld:/var/lib/mysql/client-cert.pem "${HOME}"

    # Test user for auth test
    mysql -e '
        CREATE USER
            user_sha256   IDENTIFIED WITH "sha256_password" BY "pass_sha256",
            nopass_sha256 IDENTIFIED WITH "sha256_password",
            user_caching_sha2   IDENTIFIED WITH "caching_sha2_password" BY "pass_caching_sha2",
            nopass_caching_sha2 IDENTIFIED WITH "caching_sha2_password"
            PASSWORD EXPIRE NEVER;'
    mysql -e 'GRANT RELOAD ON *.* TO user_caching_sha2;'
else
    WITH_PLUGIN=''
fi

mysql -uroot -e 'create database test_db DEFAULT CHARACTER SET utf8mb4'

mysql -u root -e "create user tester           identified ${WITH_PLUGIN} by 'testpass'; grant all on test_db.* to tester;"
mysql -u root -e "create user tester@localhost identified ${WITH_PLUGIN} by 'testpass'; grant all on test_db.* to tester@localhost;"

cp .travis/db_credentials.json tests/db_credentials.json