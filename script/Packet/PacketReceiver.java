import java.io.*;
import java.net.*;
import java.nio.file.*;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.Properties;
import java.util.concurrent.*;

public class PacketReceiver {
    static class PacketData {
        byte[] data;
        InetSocketAddress sender;
        String protocol;

        public PacketData(byte[] data, InetSocketAddress sender, String protocol) {
            this.data = data;
            this.sender = sender;
            this.protocol = protocol;
        }
    }

    static class WriterTask implements Runnable {
        private final BlockingQueue<PacketData> queue;
        private final Path logPath = Paths.get("received_packets/all_packets.log");
        private OutputStream out;

        public WriterTask(BlockingQueue<PacketData> queue) {
            this.queue = queue;
        }

        @Override
        public void run() {
            try {
                Files.createDirectories(logPath.getParent());
                out = new BufferedOutputStream(Files.newOutputStream(logPath,
                        StandardOpenOption.CREATE, StandardOpenOption.APPEND));

                while (true) {
                    PacketData packet = queue.take();
                    String timestamp = LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss.SSS"));
                    String meta = String.format("[%s] From %s:%d (%s) - %d bytes\n",
                            timestamp,
                            packet.sender.getAddress().getHostAddress(),
                            packet.sender.getPort(),
                            packet.protocol.toUpperCase(),
                            packet.data.length);

                    out.write(meta.getBytes());
                    out.write(packet.data);
                    out.write("\n\n".getBytes());
                    out.flush();
                }
            } catch (Exception e) {
                e.printStackTrace();
            } finally {
                try { if (out != null) out.close(); } catch (IOException ignored) {}
            }
        }
    }

    public static void main(String[] args) throws Exception {
        int port = loadPortFromConfig();
        BlockingQueue<PacketData> queue = new LinkedBlockingQueue<>();

        new Thread(new WriterTask(queue)).start();
        new Thread(() -> runTcpReceiver(port, queue)).start();
        new Thread(() -> runUdpReceiver(port, queue)).start();
    }

    private static int loadPortFromConfig() throws IOException {
        Properties props = new Properties();
        try (InputStream input = new FileInputStream("config.properties")) {
            props.load(input);
            int port = Integer.parseInt(props.getProperty("port"));
            System.out.println("[CONFIG] Port: " + port);
            return port;
        }
    }

    private static void runTcpReceiver(int port, BlockingQueue<PacketData> queue) {
        try (ServerSocket serverSocket = new ServerSocket()) {
            serverSocket.bind(new InetSocketAddress("0.0.0.0", port));
            System.out.println("[TCP] Listening on 0.0.0.0:" + port);

            while (true) {
                Socket socket = serverSocket.accept();
                new Thread(() -> {
                    try (Socket s = socket;
                         InputStream in = s.getInputStream()) {

                        InetSocketAddress remote = (InetSocketAddress) s.getRemoteSocketAddress();
                        ByteArrayOutputStream buffer = new ByteArrayOutputStream();
                        byte[] data = new byte[2048];
                        int len;
                        while ((len = in.read(data)) != -1) {
                            buffer.write(data, 0, len);
                        }
                        queue.offer(new PacketData(buffer.toByteArray(), remote, "TCP"));
                    } catch (IOException e) {
                        e.printStackTrace();
                    }
                }).start();
            }
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    private static void runUdpReceiver(int port, BlockingQueue<PacketData> queue) {
        try (DatagramSocket socket = new DatagramSocket(new InetSocketAddress("0.0.0.0", port))) {
            System.out.println("[UDP] Listening on 0.0.0.0:" + port);

            byte[] buf = new byte[2048];
            while (true) {
                DatagramPacket packet = new DatagramPacket(buf, buf.length);
                socket.receive(packet);
                byte[] data = new byte[packet.getLength()];
                System.arraycopy(packet.getData(), 0, data, 0, packet.getLength());

                InetSocketAddress sender = new InetSocketAddress(packet.getAddress(), packet.getPort());
                queue.offer(new PacketData(data, sender, "UDP"));
            }
        } catch (IOException e) {
            e.printStackTrace();
        }
    }
}


