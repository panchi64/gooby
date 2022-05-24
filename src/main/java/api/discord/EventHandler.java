package api.discord;

import api.discord.features.TextualTriggers;
import discord4j.core.event.domain.Event;
import discord4j.core.event.domain.command.ApplicationCommandEvent;
import discord4j.core.event.domain.lifecycle.ReadyEvent;
import discord4j.core.event.domain.message.MessageCreateEvent;
import discord4j.core.event.domain.message.MessageUpdateEvent;
import org.slf4j.LoggerFactory;
import reactor.core.publisher.Mono;

// This class is to categorize discord events (ie commands, @, textual triggers, etc)


/**
 * Handles different types of discord events by routing them to their corresponding classes.
 */
public class EventHandler {
    //    Receives an event and depending on what type of event it is, send it to the corresponding command
    public static Mono<Object> categorizeEvent(Event event, TextualTriggers triggers) {
        if (event instanceof ReadyEvent) {
            LoggerFactory.getLogger(Main.class).debug("Connection to Discord gateway established.");
            return Mono.empty();
        } else if (event instanceof MessageCreateEvent messageCreateEvent) {
            return triggers.respond(triggers.getTriggers(), messageCreateEvent);
        } else if (event instanceof MessageUpdateEvent messageUpdateEvent) {
            return Mono.empty();
        } else if (event instanceof ApplicationCommandEvent applicationCommandEvent)
            return Mono.empty();
        else
            return Mono.empty();
    }
}