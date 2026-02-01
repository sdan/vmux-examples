/**
 * Get a random container instances across N instances. This is useful for load balancing.
 * @param binding The Container's Durable Object binding
 * @param instances Number of instances to load balance across
 * @returns A promise resolving to a container stub ready to handle requests
 */
export async function getRandom(binding, instances = 3) {
    // Generate a random ID within the range of instances
    const id = Math.floor(Math.random() * instances).toString();
    // Always use idFromName for consistent behavior
    // idFromString requires a 64-hex digit string which is hard to generate
    const objectId = binding.idFromName(`instance-${id}`);
    // Return the stub for the selected instance
    return binding.get(objectId);
}
/**
 * Deprecated funtion to get random container instances. Renamed to getRandom
 * @param binding The Container's Durable Object binding
 * @param instances Number of instances to load balance across
 * @returns A promise resolving to a container stub ready to handle requests
 */
export async function loadBalance(binding, instances = 3) {
    console.warn('loadBalance is deprecated, please use getRandom instead. This will be removed in a future version.');
    return getRandom(binding, instances);
}
export const singletonContainerId = 'cf-singleton-container';
/**
 * Get a container stub
 * @param binding The Container's Durable Object binding
 * @param name The name of the instance to get, uses 'cf-singleton-container' by default
 * @returns A container stub ready to handle requests
 */
export function getContainer(binding, name = singletonContainerId) {
    const objectId = binding.idFromName(name);
    return binding.get(objectId);
}
/**
 * Return a request with the port target set correctly
 * You can use this method when you have to use `fetch` and not `containerFetch` with as it's a JSRPC method and it
 * comes with some consequences like not being able to pass WebSockets.
 *
 * @example container.fetch(switchPort(request, 8090));
 */
export function switchPort(request, port) {
    const headers = new Headers(request.headers);
    headers.set('cf-container-target-port', port.toString());
    return new Request(request, { headers });
}
//# sourceMappingURL=utils.js.map