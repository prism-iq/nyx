// myeline server - cache ultra-rapide HTTP
const std = @import("std");
const net = std.net;

pub fn main() !void {
    const address = net.Address.initIp4(.{ 127, 0, 0, 1 }, 8098);
    var server = try address.listen(.{ .reuse_address = true });
    defer server.deinit();

    std.debug.print("⚡ myeline :8098\n", .{});

    while (true) {
        const conn = try server.accept();
        defer conn.stream.close();

        var buf: [4096]u8 = undefined;
        _ = try conn.stream.read(&buf);

        const body = "{\"organ\":\"myeline\",\"status\":\"fast\"}";
        const response = "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: 35\r\n\r\n" ++ body;
        _ = try conn.stream.write(response);
    }
}
