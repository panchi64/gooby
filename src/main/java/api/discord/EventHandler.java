package api.discord;

import discord4j.core.event.domain.Event;
import discord4j.core.event.domain.lifecycle.ReadyEvent;
import discord4j.core.event.domain.message.MessageCreateEvent;
import discord4j.core.event.domain.message.MessageUpdateEvent;
import reactor.core.publisher.Mono;

// This class is to categorize messages depending on what they contain. (ie commands, @, textual triggers, etc)
public class EventHandler {
    //    Receives an event and depending on what type of event it is, send it to the corresponding command
    public static Mono<Object> categorizeEvent(Event event) {
        if (event instanceof ReadyEvent readyEvent) {
            return Mono.empty();
        } else if (event instanceof MessageCreateEvent messageCreateEvent) {
            return Mono.empty();
        } else if (event instanceof MessageUpdateEvent messageUpdateEvent) {
            return Mono.empty();
        } else
            return Mono.empty();
    }
}