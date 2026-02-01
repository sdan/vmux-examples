import type { Container } from './container';
/**
 * Get a random container instances across N instances. This is useful for load balancing.
 * @param binding The Container's Durable Object binding
 * @param instances Number of instances to load balance across
 * @returns A promise resolving to a container stub ready to handle requests
 */
export declare function getRandom<T extends Container>(binding: DurableObjectNamespace<T>, instances?: number): Promise<DurableObjectStub<T>>;
/**
 * Deprecated funtion to get random container instances. Renamed to getRandom
 * @param binding The Container's Durable Object binding
 * @param instances Number of instances to load balance across
 * @returns A promise resolving to a container stub ready to handle requests
 */
export declare function loadBalance<T extends Container>(binding: DurableObjectNamespace<T>, instances?: number): Promise<DurableObjectStub<T>>;
export declare const singletonContainerId = "cf-singleton-container";
/**
 * Get a container stub
 * @param binding The Container's Durable Object binding
 * @param name The name of the instance to get, uses 'cf-singleton-container' by default
 * @returns A container stub ready to handle requests
 */
export declare function getContainer<T extends Container>(binding: DurableObjectNamespace<T>, name?: string): DurableObjectStub<T>;
/**
 * Return a request with the port target set correctly
 * You can use this method when you have to use `fetch` and not `containerFetch` with as it's a JSRPC method and it
 * comes with some consequences like not being able to pass WebSockets.
 *
 * @example container.fetch(switchPort(request, 8090));
 */
export declare function switchPort(request: Request, port: number): Request;
