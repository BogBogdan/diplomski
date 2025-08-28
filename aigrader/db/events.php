<?php
defined('MOODLE_INTERNAL') || die();

$observers = [
    [
        'eventname'   => '\mod_quiz\event\attempt_reviewed', // Slušamo sve događaje bez izuzetka.
        'callback'    => 'local_aigrader\observer::catch_all_events', // Pozivamo funkciju u našem 'aigrader' namespace-u.
    ],
];