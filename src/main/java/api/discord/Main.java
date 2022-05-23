package api.discord;

import discord4j.core.DiscordClient;
import discord4j.core.GatewayDiscordClient;
import discord4j.core.event.domain.Event;
import io.github.cdimascio.dotenv.Dotenv;
import reactor.core.publisher.Mono;

public class Main {
    /**
     * Gets the Discord API token saved within a .env file
     *
     * @return API token from .env file
     */
    private static String envGetToken() {
        Dotenv dotenv = Dotenv.configure().directory("src/files").load();
        return dotenv.get("TOKEN");
    }

    /**
     * Initializes the Discord Client
     */
    public static void init() {
        String TOKEN = envGetToken();
        DiscordClient client = DiscordClient.create(TOKEN);

        Mono<Void> login = client.withGateway((GatewayDiscordClient gateway) ->
                gateway.on(Event.class, Categorize::categorizeEvent));
        login.block();
    }
}