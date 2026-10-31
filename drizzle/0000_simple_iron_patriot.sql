CREATE TABLE `artifacts` (
	`id` text PRIMARY KEY NOT NULL,
	`campaign` text NOT NULL,
	`sha256` text NOT NULL,
	`manifest` text NOT NULL,
	`created` integer NOT NULL
);
--> statement-breakpoint
CREATE TABLE `campaigns` (
	`id` text PRIMARY KEY NOT NULL,
	`owner` text NOT NULL,
	`name` text NOT NULL,
	`config` text NOT NULL,
	`state` text NOT NULL,
	`worker` text,
	`artifact` text,
	`created` integer NOT NULL,
	`updated` integer NOT NULL
);
--> statement-breakpoint
CREATE TABLE `jobs` (
	`id` text PRIMARY KEY NOT NULL,
	`campaign` text NOT NULL,
	`kind` text NOT NULL,
	`state` text NOT NULL,
	`worker` text,
	`report` text,
	`created` integer NOT NULL,
	`updated` integer NOT NULL
);
--> statement-breakpoint
CREATE TABLE `workers` (
	`id` text PRIMARY KEY NOT NULL,
	`seen` integer NOT NULL,
	`version` text NOT NULL
);
