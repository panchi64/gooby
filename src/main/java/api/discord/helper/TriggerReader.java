package api.discord.helper;

import java.io.FileNotFoundException;
import java.io.FileReader;
import java.util.Map;
import java.util.Scanner;
import java.util.TreeMap;

public class TriggerReader {
    public static Map<String, String[]> generateMap(String path) throws FileNotFoundException {
        Scanner scanner = new Scanner(new FileReader(path));
        Map<String, String[]> triggerMap = new TreeMap<>(String.CASE_INSENSITIVE_ORDER);
        String line;

        while (scanner.hasNext()) {
            line = scanner.nextLine();

            String[] keyValuePair = line.split("=");
            String[] responses = keyValuePair[1].split("~~");
            triggerMap.put(keyValuePair[0], responses);
        }

        return triggerMap;
    }
}
