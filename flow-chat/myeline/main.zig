// myeline.zig - vitesse, zero overhead, cache ultra-rapide
const std = @import("std");

const CacheEntry = struct {
    value: []const u8,
    timestamp: i64,
};

var cache: std.StringHashMap(CacheEntry) = undefined;
var allocator: std.mem.Allocator = undefined;

pub fn init(alloc: std.mem.Allocator) void {
    allocator = alloc;
    cache = std.StringHashMap(CacheEntry).init(allocator);
}

pub fn get(key: []const u8) ?[]const u8 {
    if (cache.get(key)) |entry| {
        const now = std.time.timestamp();
        if (now - entry.timestamp < 3600) {
            return entry.value;
        }
        _ = cache.remove(key);
    }
    return null;
}

pub fn set(key: []const u8, value: []const u8) !void {
    const key_copy = try allocator.dupe(u8, key);
    const val_copy = try allocator.dupe(u8, value);
    try cache.put(key_copy, CacheEntry{
        .value = val_copy,
        .timestamp = std.time.timestamp(),
    });
}

pub fn clear() void {
    cache.clearAndFree();
}

pub fn main() !void {
    var gpa = std.heap.GeneralPurposeAllocator(.{}){};
    init(gpa.allocator());
    std.debug.print("⚡ myeline ready - zero overhead cache\n", .{});
}
