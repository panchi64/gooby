import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class Main {
    public static void main(String[] args) {
        final Logger logger = LoggerFactory.getLogger(api.discord.Main.class);

//        Initialize the discord bot
        logger.debug("Initializing discord bot ...");
        api.discord.Main.init();

//        Bot cleanup on JVM shutdown
        Runtime.getRuntime().addShutdownHook(new Thread(() -> {
                    logger.debug("Cleaning up and storing information.");
                    api.discord.Main.shutdown();
                })
        );
        logger.debug("Application Terminating ...");
    }
}

