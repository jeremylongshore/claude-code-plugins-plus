import { createHash } from "node:crypto";
import { Command } from "commander";
import { type Contract, ContractSchema } from "../core/contracts/schema.js";
import { readContracts, writeContracts } from "../core/contracts/storage.js";

export const contractCommand = new Command("contract").description("Manage verification contracts");

contractCommand
	.command("add")
	.description("Add a new contract")
	.requiredOption("--type <type>", "Contract type")
	.option("--description <text>", "Contract description", "")
	.option("--params <json>", "Contract parameters as JSON", "{}")
	.option("--severity <level>", "blocking or warning", "blocking")
	.option("--json", "Output as JSON", false)
	.action((opts) => {
		const params = JSON.parse(opts.params);
		const id = createHash("sha256")
			.update(`${opts.type}:${opts.params}:${Date.now()}`)
			.digest("hex")
			.slice(0, 12);

		const contract: Contract = ContractSchema.parse({
			id,
			description: opts.description || `${opts.type} contract`,
			type: opts.type,
			params,
			severity: opts.severity,
		});

		const contracts = readContracts();
		contracts.push(contract);
		writeContracts(contracts);

		if (opts.json) {
			process.stdout.write(`${JSON.stringify(contract, null, 2)}\n`);
		} else {
			console.log(`Contract added: ${contract.id} (${contract.type})`);
		}
	});

contractCommand
	.command("list")
	.description("List all contracts")
	.option("--json", "Output as JSON", false)
	.action((opts) => {
		const contracts = readContracts();
		if (opts.json) {
			process.stdout.write(`${JSON.stringify(contracts, null, 2)}\n`);
		} else {
			if (contracts.length === 0) {
				console.log("No contracts defined.");
				return;
			}
			for (const c of contracts) {
				console.log(`  ${c.id} [${c.severity}] ${c.type}: ${c.description}`);
			}
		}
	});

contractCommand
	.command("remove")
	.description("Remove a contract by ID")
	.requiredOption("--id <id>", "Contract ID to remove")
	.option("--json", "Output as JSON", false)
	.action((opts) => {
		const contracts = readContracts();
		const idx = contracts.findIndex((c) => c.id === opts.id);
		if (idx === -1) {
			if (opts.json) {
				process.stdout.write(`${JSON.stringify({ error: "not_found", id: opts.id })}\n`);
			} else {
				console.error(`Contract not found: ${opts.id}`);
			}
			process.exit(1);
		}
		const removed = contracts.splice(idx, 1)[0];
		writeContracts(contracts);
		if (opts.json) {
			process.stdout.write(`${JSON.stringify(removed, null, 2)}\n`);
		} else {
			console.log(`Contract removed: ${removed.id}`);
		}
	});
