import { storage } from "./storage";

export async function seedDatabase() {
  const existing = await storage.getAllReturns();
  if (existing.length > 0) return;

  const returns = [
    {
      orderId: "OD4827391056",
      productName: "boAt Rockerz 450 Bluetooth Headphones",
      platform: "amazon" as const,
      reason: "defective" as const,
      amount: 1499,
      description: "Left speaker stopped working after 2 days of use. No audio output from the left side.",
    },
    {
      orderId: "FL9283746512",
      productName: "Nike Air Max 270 Running Shoes - Size 9",
      platform: "flipkart" as const,
      reason: "size_issue" as const,
      amount: 8995,
      description: "Ordered size 9 but received size 8. Need the correct size or full refund.",
    },
    {
      orderId: "MN7364829150",
      productName: "Levi's Men's Slim Fit Jeans - Blue",
      platform: "myntra" as const,
      reason: "not_as_described" as const,
      amount: 2499,
      description: "Color is completely different from what was shown. Expected dark blue, received light grey.",
    },
    {
      orderId: "MS5019283746",
      productName: "Samsung 20000mAh Power Bank",
      platform: "meesho" as const,
      reason: "damaged" as const,
      amount: 1299,
      description: "Package arrived with visible dents. Power bank has a cracked casing and doesn't charge.",
    },
    {
      orderId: "AJ6182739405",
      productName: "Puma RS-X Sneakers - White/Red",
      platform: "ajio" as const,
      reason: "wrong_item" as const,
      amount: 6999,
      description: "Received completely wrong product. Ordered white/red sneakers but got black sandals.",
    },
  ];

  for (const ret of returns) {
    await storage.createReturn(ret);
  }

  const allReturns = await storage.getAllReturns();

  if (allReturns[0]) {
    await storage.updateReturnStatus(allReturns[0].id, "pickup_scheduled");
    await storage.addStatusHistory({
      returnRequestId: allReturns[0].id,
      status: "pickup_scheduled",
      note: "Pickup scheduled for tomorrow between 10 AM - 2 PM",
    });
  }

  if (allReturns[1]) {
    const statuses = ["pickup_scheduled", "picked_up", "in_transit", "received", "inspecting", "refund_initiated", "refund_completed"] as const;
    const notes = [
      "Pickup scheduled for 15 Mar 2026",
      "Package picked up by courier",
      "Package in transit to warehouse",
      "Package received at warehouse",
      "Quality check in progress",
      "Refund of ₹8,995 initiated to bank account",
      "Refund credited to bank account",
    ];
    for (let i = 0; i < statuses.length; i++) {
      await storage.updateReturnStatus(allReturns[1].id, statuses[i]);
      await storage.addStatusHistory({
        returnRequestId: allReturns[1].id,
        status: statuses[i],
        note: notes[i],
      });
    }
  }

  if (allReturns[2]) {
    const statuses = ["pickup_scheduled", "picked_up", "in_transit"] as const;
    const notes = [
      "Pickup confirmed for 18 Mar 2026",
      "Courier picked up the package",
      "En route to Myntra warehouse, Bengaluru",
    ];
    for (let i = 0; i < statuses.length; i++) {
      await storage.updateReturnStatus(allReturns[2].id, statuses[i]);
      await storage.addStatusHistory({
        returnRequestId: allReturns[2].id,
        status: statuses[i],
        note: notes[i],
      });
    }
  }

  if (allReturns[3]) {
    await storage.updateReturnStatus(allReturns[3].id, "pickup_scheduled");
    await storage.addStatusHistory({
      returnRequestId: allReturns[3].id,
      status: "pickup_scheduled",
      note: "Courier will arrive between 2 PM - 6 PM today",
    });
    await storage.updateReturnStatus(allReturns[3].id, "picked_up");
    await storage.addStatusHistory({
      returnRequestId: allReturns[3].id,
      status: "picked_up",
      note: "Package collected by delivery partner",
    });
  }

  console.log("Database seeded with sample return requests");
}
