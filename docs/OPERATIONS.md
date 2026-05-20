# cenabobot operations

cenabobot is a private Telegram meal suggestion bot.

Production runs on the Hetzner VPS named resfactae.

Main production path:

    /opt/cenabobot

## Core production rule

The VPS bot is the permanent bot instance.

Do not run another bot instance with the same Telegram token while production is polling Telegram.

If you run the bot locally with the same token while the VPS bot is running, Telegram will return a conflict error because only one long-polling instance can use the token at a time.

## Secrets

The following files contain secrets and must never be committed, pasted, or shared:

    .env
    .env.production

The Telegram bot token is already configured on the VPS.

The production Postgres password is in .env.production on the VPS.

## SSH

Use your real server IP or SSH host alias:

    ssh root@YOUR_SERVER_IP

Then go to the project:

    cd /opt/cenabobot

## Check production status

    cd /opt/cenabobot
    docker compose -f docker-compose.prod.yml --env-file .env.production ps

## View bot logs

    cd /opt/cenabobot
    docker compose -f docker-compose.prod.yml --env-file .env.production logs -f bot

Stop following logs with Ctrl+C.

This does not stop the bot.

## Restart the bot

    cd /opt/cenabobot
    docker compose -f docker-compose.prod.yml --env-file .env.production restart bot

## Update production code from GitHub

Use this only after changes are committed and pushed to the branch you want to deploy.

For normal production updates from main:

    cd /opt/cenabobot
    git checkout main
    git pull --ff-only origin main
    docker compose -f docker-compose.prod.yml --env-file .env.production up -d --build

Check status after rebuild:

    docker compose -f docker-compose.prod.yml --env-file .env.production ps

Check logs:

    docker compose -f docker-compose.prod.yml --env-file .env.production logs -f bot

## Run recipe validation on the VPS

This does not start a second Telegram polling bot.

    cd /opt/cenabobot
    docker compose -f docker-compose.prod.yml --env-file .env.production run --rm --no-deps bot python scripts/validate_recipes.py

Warnings mean the catalogue may need review.

Errors should be fixed before importing recipes.

## Import recipes

Only run this after validation passes.

    cd /opt/cenabobot
    docker compose -f docker-compose.prod.yml --env-file .env.production run --rm bot python scripts/import_recipes.py

This writes recipe catalogue data to production Postgres.

## Backup database

There is a helper script:

    scripts/backup_db.sh

Run it from the project root:

    cd /opt/cenabobot
    chmod +x scripts/backup_db.sh
    ./scripts/backup_db.sh

Backups are written to:

    /opt/cenabobot/backups/

Example:

    backups/cenabobot-20260520-213000.sql

## Copy a backup to local Mac

From your Mac, not from inside the VPS SSH session:

    scp root@YOUR_SERVER_IP:/opt/cenabobot/backups/cenabobot-YYYYMMDD-HHMMSS.sql ~/Downloads/

Replace the filename with the real backup file.

To list backups on the VPS:

    cd /opt/cenabobot
    ls -lh backups

## Restore database

Be careful: restore can overwrite production data.

Do not rely on restore until it has been tested on a safe copy.

A future V2 maintenance pass should add a tested restore script.

For now, before restoring production:

1. Make a fresh backup.
2. Copy the backup away from the VPS.
3. Test restore on a disposable/local database first.
4. Only then restore production.

## Stop the bot

    cd /opt/cenabobot
    docker compose -f docker-compose.prod.yml --env-file .env.production stop bot

## Start the bot again

    cd /opt/cenabobot
    docker compose -f docker-compose.prod.yml --env-file .env.production up -d bot

## Production safety reminders

- Do not commit .env or .env.production.
- Do not paste the Telegram token into ChatGPT, GitHub, or terminal history unnecessarily.
- Do not expose Postgres publicly.
- The Hetzner firewall only needs SSH open for now.
- The bot uses Telegram long polling, not webhooks.
- There is no public HTTP endpoint.
- There should be only one active polling instance per Telegram token.
