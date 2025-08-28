<?php
defined('MOODLE_INTERNAL') || die();

class local_aigrader_observer {

    /**
     * KORAK 1: OCENJIVANJE I OSTAVLJANJE TRAGA
     * Okida se kada korisnik preda kviz.
     * Ocenjuje esejska pitanja i ostavlja specifičan komentar kao "trag".
     */
    public static function quiz_attempt_submitted(\mod_quiz\event\attempt_submitted $event) {
        $attemptid = $event->get_data()['attemptid'];
        $attemptobj = quiz_create_attempt_handling_object($attemptid);
        if (!$attemptobj) {
            return;
        }

        $slots = $attemptobj->get_slots();
        $questions = $attemptobj->get_questions();

        foreach ($slots as $slot) {
            $question = $questions[$slot];
            if ($question->qtype === 'essay') {
                $qa = $attemptobj->get_question_attempt($slot);
                $state = $qa->get_state();
                question_set_grade($question, $state, 1.0);
                
                // Ovaj komentar je naš ključni "trag".
                question_save_comment($question, $state, "Automatski ocenjeno sa max poena.");
            }
        }
    }

    /**
     * KORAK 2: DETEKCIJA TRAGA I ISPIS U KONZOLU
     * Okida se kada korisnik POGLEDA stranicu sa pregledom pokušaja.
     * Proverava da li postoji "trag" i ako postoji, ispisuje poruku u konzolu.
     */
    public static function quiz_attempt_viewed(\mod_quiz\event\attempt_viewed $event) {
        global $PAGE, $USER; // Potreban nam je globalni $PAGE objekat za ubacivanje JS

        // Marker koji nam kaže da li je AI Grader radio
        $aigraded_this_attempt = false;
        
        // Naš "trag" koji tražimo
        $comment_to_find = "Automatski ocenjeno sa max poena.";

        $attemptid = $event->get_data()['attemptid'];
        $attemptobj = quiz_create_attempt_handling_object($attemptid);
        if (!$attemptobj) {
            return;
        }

        // Prolazimo kroz pitanja da nađemo naš "trag"
        $slots = $attemptobj->get_slots();
        foreach ($slots as $slot) {
            $qa = $attemptobj->get_question_attempt($slot);
            $state = $qa->get_state();
            
            // Proveravamo da li komentar pitanja odgovara našem tragu
            if (isset($state->comment) && $state->comment === $comment_to_find) {
                $aigraded_this_attempt = true;
                break; // Našli smo, ne moramo dalje da tražimo
            }
        }
        
        // Ako je naš AI Grader ocenio bar jedno pitanje u ovom pokušaju...
        if ($aigraded_this_attempt) {
            // ...onda ubacujemo JavaScript kod na stranicu!
            $message = "AI Grader je upravo automatski ocenio esej za korisnika {$USER->firstname} na kvizu ID: {$event->courseid}.";
            
            // Koristimo Moodle API za slanje poruke u JS konzolu.
            // addslashes() je tu da spreči JS greške ako poruka sadrži navodnike.
            $PAGE->requires->js_init_code('console.log("' . addslashes($message) . '");');
        }
    }
}