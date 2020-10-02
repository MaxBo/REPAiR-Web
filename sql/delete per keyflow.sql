/* DELETES ALL FLOW DATA IN THE RIGHT ORDER:
   1) ALL CHANGES MADE BY THE STRATEGY
   2) ALL SOLUTION PARTS
   3) FLOWS
   4) FLOW SUPPORTING DATA (ACTORS, ACTIVITIES, MATERIALS, ETC.)

TO USE:
   CHOOSE AND CHANGE keyflow_id = X INTO THE CORRECT KEYFLOW_ID FROM THE TABLE asmfa_keyflowincasestudy
 */


delete from changes_implementationarea
-- select * from changes_implementationquantity
    where implementation_id in
          (select id
           from changes_solutioninstrategy
           where strategy_id in
                                               (select changes_strategy.id
                                                from changes_strategy
                                                where changes_strategy.keyflow_id = 5));

delete from changes_implementationquantity
-- select * from changes_implementationquantity
    where implementation_id in
          (select id
           from changes_solutioninstrategy
           where strategy_id in
                                               (select changes_strategy.id
                                                from changes_strategy
                                                where changes_strategy.keyflow_id = 5));

delete from changes_solutioninstrategy_participants
-- select * from changes_solutioninstrategy_participants
    where solutioninstrategy_id in
          (select id
           from changes_solutioninstrategy
           where strategy_id in
                                               (select changes_strategy.id
                                                from changes_strategy
                                                where changes_strategy.keyflow_id = 5));

delete from changes_solutioninstrategy where strategy_id in
-- select * from changes_solutioninstrategy where strategy_id in
                                               (select changes_strategy.id
                                                from changes_strategy
                                                where changes_strategy.keyflow_id = 5);

delete from asmfa_fractionflow where strategy_id in
-- select * from asmfa_fractionflow where strategy_id in
                                               (select changes_strategy.id
                                                from changes_strategy
                                                where changes_strategy.keyflow_id = 5);

delete from asmfa_strategyfractionflow where strategy_id in
-- select * from asmfa_strategyfractionflow where strategy_id in
                                               (select changes_strategy.id
                                                from changes_strategy
                                                where changes_strategy.keyflow_id = 5);

delete from changes_strategy where keyflow_id = 5;
-- select * from changes_strategy wherekeyflow_id = 5;

delete from asmfa_fractionflow where keyflow_id = 5 ;
-- select * from asmfa_fractionflow wherekeyflow_id = 5 ;

delete from asmfa_actor2actor where keyflow_id = 5 ;
-- select * from asmfa_actor2actor wherekeyflow_id = 5 ;

delete from asmfa_actorstock where keyflow_id = 5 ;
-- select * from asmfa_actorstock wherekeyflow_id = 5 ;

delete from asmfa_productfraction where id in
-- select * from asmfa_productfraction where id in
                                      (select asmfa_productfraction.id
                                       from asmfa_composition join asmfa_productfraction
                                                on asmfa_composition.id = asmfa_productfraction.composition_id
                                      where asmfa_composition.keyflow_id = 5);


delete from asmfa_waste where composition_ptr_id in
-- select * from asmfa_waste where composition_ptr_id in
                              (select id
                               from asmfa_composition
                               where asmfa_composition.keyflow_id = 5);


delete from asmfa_product where composition_ptr_id in
-- select * from asmfa_product where composition_ptr_id in
                              (select id
                               from asmfa_composition
                               where asmfa_composition.keyflow_id = 5);

delete from asmfa_composition where keyflow_id = 5;
-- select * from asmfa_composition wherekeyflow_id = 5;

delete from statusquo_flowfilter_areas where flowfilter_id in
-- select * from statusquo_flowfilter_areas where flowfilter_id in
                                               (select id
                                                from statusquo_flowfilter
                                                where keyflow_id = 5);

delete from statusquo_indicatorflow_materials where material_id in
-- select * from statusquo_indicatorflow_materials where material_id in
                                               (select id
                                                from asmfa_material
                                                where keyflow_id = 5);

delete from statusquo_flowfilter where keyflow_id = 5;
-- select * from statusquo_flowfilter wherekeyflow_id = 5;

delete from changes_affectedflow where solution_part_id in
-- select * from changes_affectedflow where solution_part_id in
                                          (select id
                                           from changes_solutionpart
                                           where flow_reference_id in
                                                 (select id
                                                     from changes_flowreference
                                                     where material_id in
                                                            (select id
                                                             from asmfa_material
                                                             where keyflow_id = 5)));

delete from changes_solutionpart where flow_reference_id in
-- select * from changes_solutionpart where flow_reference_id in
                                          (select id
                                           from changes_flowreference
                                           where material_id in
                                                  (select id
                                                   from asmfa_material
                                                   where keyflow_id = 5));

delete from changes_flowreference where material_id in
-- select * from changes_flowreference where material_id in
                                          (select id
                                           from asmfa_material
                                           where keyflow_id = 5);

delete from changes_flowreference where destination_activity_id in
-- select * from changes_flowreference where material_id in
                                          (select asmfa_activity.id
                                            from asmfa_activity join asmfa_activitygroup
                                                     on (asmfa_activity.activitygroup_id = asmfa_activitygroup.id)
                                            where asmfa_activitygroup.keyflow_id = 5);

delete from asmfa_material where keyflow_id = 5;
-- select * from asmfa_material wherekeyflow_id = 5;

delete from asmfa_administrativelocation where id in
-- select * from asmfa_administrativelocation where id in
																							 (select asmfa_administrativelocation.id
                                                from asmfa_administrativelocation join actor_complete
                                                         on (asmfa_administrativelocation.actor_id = actor_complete.id)
                                                where actor_complete.keyflow_id = 5);

delete from asmfa_operationallocation where id in
-- select * from asmfa_administrativelocation where id in
																							 (select asmfa_operationallocation.id
                                                from asmfa_operationallocation join actor_complete
                                                         on (asmfa_operationallocation.actor_id = actor_complete.id)
                                                where actor_complete.keyflow_id = 5);

delete from asmfa_actor where id in
-- select * from asmfa_actor where id in
																							 (select asmfa_actor.id
                                                from asmfa_actor join actor_complete
                                                         using (id)
                                                where actor_complete.keyflow_id = 5);

-- delete from changes_solutionpart where implementation_flow_destination_activity_id in
-- delete from changes_affectedflow where origin_activity_id in
--                                      (select asmfa_activity.id
--                                   from asmfa_activity join asmfa_activitygroup
--                                            on (asmfa_activity.activitygroup_id = asmfa_activitygroup.id)
--                                   where asmfa_activitygroup.keyflow_id = 5);

delete from asmfa_activity where id in
-- select * from asmfa_activity where id in
																 (select asmfa_activity.id
                                  from asmfa_activity join asmfa_activitygroup
                                           on (asmfa_activity.activitygroup_id = asmfa_activitygroup.id)
                                  where asmfa_activitygroup.keyflow_id = 5);

delete from asmfa_activitygroup where keyflow_id = 5;
-- select * from asmfa_activitygroup wherekeyflow_id = 5;