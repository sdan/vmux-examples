/**
 * Repro for keepAlive container eviction issue
 * Run with: npx wrangler dev keepalive-test.ts --local=false
 */

import { getSandbox, Sandbox } from "@cloudflare/sandbox";

export { Sandbox };

export default {
  async fetch(request: Request, env: { Sandbox: DurableObjectNamespace }): Promise<Response> {
    const url = new URL(request.url);
    const jobId = "keepalive-test-001";

    // Step 1: Create sandbox with keepAlive
    if (url.pathname === "/start") {
      const sandbox = getSandbox(env.Sandbox, jobId, { keepAlive: true, sleepAfter: '168h' });
      await sandbox.setKeepAlive(true);

      // Write a marker file
      await sandbox.writeFile("/tmp/marker.txt", `created at ${new Date().toISOString()}`);
      const result = await sandbox.exec("cat /tmp/marker.txt");

      return Response.json({
        status: "started",
        marker: result.stdout,
        message: "Now wait 10+ minutes and hit /check"
      });
    }

    // Step 2: Check if container survived
    if (url.pathname === "/check") {
      const sandbox = getSandbox(env.Sandbox, jobId, { keepAlive: true, sleepAfter: '168h' });

      try {
        const result = await sandbox.exec("cat /tmp/marker.txt 2>&1 || echo 'FILE_NOT_FOUND'");
        const isAlive = !result.stdout?.includes("FILE_NOT_FOUND") && !result.stdout?.includes("No such file");

        return Response.json({
          status: isAlive ? "ALIVE - container survived!" : "DEAD - container was evicted",
          output: result.stdout,
          timestamp: new Date().toISOString()
        });
      } catch (e) {
        return Response.json({
          status: "ERROR",
          error: String(e)
        });
      }
    }

    // Step 3: Cleanup
    if (url.pathname === "/destroy") {
      const sandbox = getSandbox(env.Sandbox, jobId, { keepAlive: true });
      await sandbox.destroy();
      return Response.json({ status: "destroyed" });
    }

    return Response.json({
      endpoints: {
        "/start": "Create sandbox with keepAlive=true and write marker file",
        "/check": "Check if marker file still exists (container survived)",
        "/destroy": "Cleanup the sandbox"
      }
    });
  }
};
