FROM python:2.7-slim
LABEL "project.home"="https://github.com/BitBotFactory/poloniexlendingbot"

#
# Build: docker build -t <your_id>/pololendingbot .
# Run: docker run -d -v /pololendingbot_data:/data -p 8000:8000 <your_id>/pololendingbot
#

WORKDIR /usr/src/app

COPY requirements.txt .
RUN pip install --no-cache-dir -r ./requirements.txt

COPY . .

VOLUME /data

RUN ln -s /data/market_data market_data; \
    ln -s /data/log/botlog.json www/botlog.json

EXPOSE 8000

CMD ["python", "lendingbot.py", "-cfg", "/data/conf/default.cfg"]
