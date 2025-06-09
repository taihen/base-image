import java.net.InetAddress;
import java.net.UnknownHostException;

public class Main {
    public static void main(String[] args) {
        try {
            String hostname = InetAddress.getLocalHost().getHostName();
            System.out.printf("Hello from %s!%n", hostname);
        } catch (UnknownHostException e) {
            System.out.println("Hello from unknown host!");
        }
        
        System.out.printf("Running on %s/%s%n", 
            System.getProperty("os.name"), 
            System.getProperty("os.arch"));
        System.out.printf("Built with Java %s%n", 
            System.getProperty("java.version"));
    }
} 