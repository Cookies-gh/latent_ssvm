import numpy as np

from time import time
import logging

from frankwolfe_ssvm import FrankWolfeSSVM
from one_slack_ssvm import OneSlackSSVM
from latent_structured_svm import LatentSSVM
from subgradient_ssvm import SubgradientSSVM
from over import Over
from over_weak import OverWeak
from subgrad import Subgrad
from heterogenous_crf import HCRF

from results import ExperimentResult, experiment
from utils import load_syntetic, load_msrc, load_binary_syntetic

@experiment
def syntetic_weak(n_full=10, n_train=200, C=0.1, dataset=1, latent_iter=15,
                  max_iter=500, inner_tol=0.001, outer_tol=0.01, min_changes=0,
                  initialize=True, alpha=0.1, n_inference_iter=5,
                  inactive_window=50, inactive_threshold=1e-5,
                  warm_start=False, inference_cache=0,
                  save_inner_w=False, inference_method='gco'):
    # save parameters as meta
    meta_data = locals()

    logger = logging.getLogger(__name__)

    crf = HCRF(n_states=10, n_features=10, n_edge_features=2, alpha=alpha,
               inference_method=inference_method, n_iter=n_inference_iter)
    base_clf = OneSlackSSVM(crf, verbose=2, n_jobs=4,
                            max_iter=max_iter, tol=inner_tol, C=C,
                            inference_cache=inference_cache,
                            inactive_window=inactive_window,
                            inactive_threshold=inactive_threshold)
    clf = LatentSSVM(base_clf, latent_iter=latent_iter, verbose=2,
                     tol=outer_tol, min_changes=min_changes, n_jobs=4)

    x_train, y_train, y_train_full, x_test, y_test = \
        load_syntetic(dataset, n_full, n_train)

    start = time()
    clf.fit(x_train, y_train,
            initialize=initialize, warm_start=warm_start,
            save_inner_w=save_inner_w)
    stop = time()

    train_score = clf.score(x_train, y_train_full)
    test_score = clf.score(x_test, y_test)
    time_elapsed = stop - start

    logger.info('============================================================')
    logger.info('Score on train set: %f', train_score)
    logger.info('Score on test set: %f', test_score)
    logger.info('Norm of weight vector: |w|=%f', np.linalg.norm(clf.w))
    logger.info('Elapsed time: %f s', time_elapsed)

    test_scores = []
    for score in clf.staged_score(x_test, y_test):
        test_scores.append(score)

    train_scores = []
    for score in clf.staged_score(x_train, y_train_full):
        train_scores.append(score)

    raw_scores = []
    for score in clf.staged_score2(x_train, y_train):
        raw_scores.append(score)

    exp_data = clf._get_data()
    exp_data['test_scores'] = np.array(test_scores)
    exp_data['train_scores'] = np.array(train_scores)
    exp_data['raw_scores'] = np.array(raw_scores)

    meta_data['dataset_name'] = 'syntetic'
    meta_data['annotation_type'] = 'image-level labelling'
    meta_data['label_type'] = 'full+weak'
    meta_data['train_score'] = train_score
    meta_data['test_score'] = test_score
    meta_data['time_elapsed'] = time_elapsed
    meta_data['iter_done'] = clf.iter_done

    return ExperimentResult(exp_data, meta_data)


@experiment
def msrc_weak(n_full=20, n_train=276, C=100, latent_iter=25,
              max_iter=500, inner_tol=0.001, outer_tol=0.01, min_changes=0,
              initialize=True, alpha=0.1, n_inference_iter=5,
              inactive_window=50, inactive_threshold=1e-5,
              warm_start=False, inference_cache=0,
              save_inner_w=False, inference_method='gco'):
    meta_data = locals()

    logger = logging.getLogger(__name__)

    crf = HCRF(n_states=24, n_features=2028, n_edge_features=4, alpha=alpha,
               inference_method=inference_method, n_iter=n_inference_iter)
    base_clf = OneSlackSSVM(crf, verbose=2, n_jobs=4,
                            tol=inner_tol, max_iter=max_iter, C=C,
                            inference_cache=inference_cache,
                            inactive_window=inactive_window,
                            inactive_threshold=inactive_threshold)
    clf = LatentSSVM(base_clf, latent_iter=latent_iter, verbose=2,
                     tol=outer_tol, min_changes=min_changes, n_jobs=4)

    x_train, y_train, y_train_full, x_test, y_test = \
        load_msrc(n_full, n_train)

    start = time()
    clf.fit(x_train, y_train,
            initialize=initialize,
            warm_start=warm_start,
            save_inner_w=save_inner_w)
    stop = time()

    train_score = clf.score(x_train, y_train_full)
    test_score = clf.score(x_test, y_test)
    time_elapsed = stop - start 

    logger.info('============================================================')
    logger.info('Score on train set: %f', train_score)
    logger.info('Score on test set: %f', test_score)
    logger.info('Norm of weight vector: |w|=%f', np.linalg.norm(clf.w))
    logger.info('Elapsed time: %f s', time_elapsed)

    test_scores = []
    for score in clf.staged_score(x_test, y_test):
        test_scores.append(score)

    train_scores = []
    for score in clf.staged_score(x_train, y_train_full):
        train_scores.append(score)

    raw_scores = []
    for score in clf.staged_score2(x_train, y_train):
        raw_scores.append(score)

    exp_data = clf._get_data()
    exp_data['test_scores'] = np.array(test_scores)
    exp_data['train_scores'] = np.array(train_scores)
    exp_data['raw_scores'] = np.array(raw_scores)

    meta_data['dataset_name'] = 'msrc'
    meta_data['annotation_type'] = 'image-level labelling'
    meta_data['label_type'] = 'full+weak'
    meta_data['train_score'] = train_score
    meta_data['test_score'] = test_score
    meta_data['time_elapsed'] = time_elapsed
    meta_data['iter_done'] = clf.iter_done

    return ExperimentResult(exp_data, meta_data)


## FULL Frank-Wolfe experiments

@experiment
def msrc_full_fw(n_train=276, C=100, max_iter=500, check_dual_every=50,
                 inference_method='gco', n_inference_iter=5):
    # save parameters as meta
    meta_data = locals()

    logger = logging.getLogger(__name__)

    crf = HCRF(n_states=24, n_features=2028, n_edge_features=4, alpha=1,
               inference_method=inference_method, n_iter=n_inference_iter)
    clf = FrankWolfeSSVM(crf, verbose=2, n_jobs=1,
                         check_dual_every=check_dual_every, max_iter=max_iter, C=C)

    x_train, y_train, y_train_full, x_test, y_test = \
        load_msrc(n_train, n_train)

    logger.info('start training')

    start = time()
    clf.fit(x_train, y_train, Xtest=x_test, Ytest=y_test)
    stop = time()

    train_score = clf.score(x_train, y_train_full)
    test_score = clf.score(x_test, y_test)
    time_elapsed = stop - start

    logger.info('============================================================')
    logger.info('Score on train set: %f', train_score)
    logger.info('Score on test set: %f', test_score)
    logger.info('Elapsed time: %f s', time_elapsed)

    exp_data = {}

    exp_data['timestamps'] = clf.timestamps_
    exp_data['primal_objective'] = clf.primal_objective_curve_
    exp_data['objective'] = clf.objective_curve_
    exp_data['w_history'] = clf.w_history
    exp_data['test_scores'] = clf.test_scores
    exp_data['train_scores'] = clf.train_scores
    exp_data['w'] = clf.w

    meta_data['dataset_name'] = 'syntetic'
    meta_data['annotation_type'] = 'full'
    meta_data['label_type'] = 'full'
    meta_data['trainer'] = 'frank-wolfe'
    meta_data['train_score'] = train_score
    meta_data['test_score'] = test_score
    meta_data['time_elapsed'] = time_elapsed

    return ExperimentResult(exp_data, meta_data)


@experiment
def syntetic_full_fw(n_train=100, C=0.1, dataset=1,
                     max_iter=1000, n_inference_iter=5,
                     check_dual_every=10, test_samples=50,
                     inference_method='gco'):
    # save parameters as meta
    meta_data = locals()

    logger = logging.getLogger(__name__)

    crf = HCRF(n_states=10, n_features=10, n_edge_features=2, alpha=1,
               inference_method=inference_method, n_iter=n_inference_iter)
    clf = FrankWolfeSSVM(crf, verbose=2, n_jobs=1, check_dual_every=check_dual_every,
                         max_iter=max_iter, C=C)

    x_train, y_train, y_train_full, x_test, y_test = \
        load_syntetic(dataset, n_train, n_train)

    logger.info('start training')

    start = time()
    clf.fit(x_train, y_train, Xtest=x_test[:test_samples], Ytest=y_test[:test_samples])
    stop = time()

    train_score = clf.score(x_train, y_train_full)
    test_score = clf.score(x_test, y_test)
    time_elapsed = stop - start

    logger.info('============================================================')
    logger.info('Score on train set: %f', train_score)
    logger.info('Score on test set: %f', test_score)
    logger.info('Elapsed time: %f s', time_elapsed)

    exp_data = {}

    exp_data['timestamps'] = clf.timestamps_
    exp_data['primal_objective'] = clf.primal_objective_curve_
    exp_data['objective'] = clf.objective_curve_
    exp_data['w_history'] = clf.w_history
    exp_data['test_scores'] = clf.test_scores
    exp_data['train_scores'] = clf.train_scores
    exp_data['w'] = clf.w

    meta_data['dataset_name'] = 'syntetic'
    meta_data['annotation_type'] = 'full'
    meta_data['label_type'] = 'full'
    meta_data['trainer'] = 'frank-wolfe'
    meta_data['train_score'] = train_score
    meta_data['test_score'] = test_score
    meta_data['time_elapsed'] = time_elapsed

    return ExperimentResult(exp_data, meta_data)


## Komodakis overgenerating

def compute_score(crf, w, X, Y, invert=False, relaxed=False):
    losses = [crf.loss(y, crf.inference(x, w, invert=invert, relaxed=relaxed)) / float(np.sum(y.weights))
              for x, y in zip(X, Y)]
    return 1. - np.sum(losses) / float(len(X))


@experiment
def syntetic_over(n_train=100, C=1, dataset=1,
                  max_iter=100, verbose=1,
                  test_samples=10, check_every=10,
                  test_method='gco', test_n_iter=5, relaxed_test=False):
    # save parameters as meta
    meta_data = locals()

    logger = logging.getLogger(__name__)

    crf = HCRF(n_states=10, n_features=10, n_edge_features=2, alpha=1,
               inference_method=test_method, n_iter=test_n_iter)
    trainer = Over(n_states=10, n_features=10, n_edge_features=2,
                   C=C, max_iter=max_iter, verbose=verbose, check_every=check_every)

    x_train, y_train, y_train_full, x_test, y_test = \
        load_syntetic(dataset, n_train, n_train)
    x_test = x_test[:test_samples]
    y_test = y_test[:test_samples]

    logger.info('start training')

    start = time()
    trainer.fit(x_train, y_train_full,
                train_scorer=lambda w: compute_score(crf, w, x_train, y_train, invert=True, relaxed=relaxed_test),
                test_scorer=lambda w: compute_score(crf, w, x_test, y_test, invert=True, relaxed=relaxed_test),
                decompose='grid')
    stop = time()
    time_elapsed = stop - start

    logger.info('testing')

    test_score = compute_score(crf, trainer.w, x_test, y_test, invert=True, relaxed=relaxed_test)
    train_score = compute_score(crf, trainer.w, x_train, y_train, invert=True, relaxed=relaxed_test)

    logger.info('========================================')
    logger.info('train score: %f', train_score)
    logger.info('test score: %f', test_score)

    exp_data = {}

    exp_data['timestamps'] = trainer.timestamps
    exp_data['objective'] = trainer.objective_curve
    exp_data['w'] = trainer.w
    exp_data['train_scores'] = trainer.train_score
    exp_data['test_scores'] = trainer.test_score
    exp_data['w_history'] = trainer.w_history

    meta_data['dataset_name'] = 'syntetic'
    meta_data['annotation_type'] = 'full'
    meta_data['label_type'] = 'full'
    meta_data['trainer'] = 'komodakis'
    meta_data['train_score'] = train_score
    meta_data['test_score'] = test_score
    meta_data['time_elapsed'] = time_elapsed

    return ExperimentResult(exp_data, meta_data)


@experiment
def syntetic_over_weak(n_train_full=10, n_train=100, C=1, dataset=1,
                       max_iter=100, verbose=1,
                       test_samples=10, check_every=10,
                       test_method='gco', test_n_iter=5, relaxed_test=False,
                       alpha=1, n_iter=5, complete_every=10,
                       update_w_every=5, update_mu=20,
                       use_latent_first_iter=500, undergenerating_weak=False,
                       smd=False):
    # save parameters as meta
    meta_data = locals()

    logger = logging.getLogger(__name__)

    crf_test = HCRF(n_states=10, n_features=10, n_edge_features=2,
                    inference_method=test_method, n_iter=test_n_iter)
    crf_latent = HCRF(n_states=10, n_features=10, n_edge_features=2,
                      alpha=alpha, inference_method='gco', n_iter=n_iter)
    trainer = OverWeak(crf_latent, n_states=10, n_features=10, n_edge_features=2,
                       C=C, max_iter=max_iter, verbose=verbose, check_every=check_every,
                       complete_every=complete_every, alpha=alpha, update_w_every=update_w_every,
                       update_mu=update_mu)

    x_train, y_train, y_train_full, x_test, y_test = \
        load_syntetic(dataset, n_train_full, n_train)
    x_test = x_test[:test_samples]
    y_test = y_test[:test_samples]

    logger.info('start training')

    start = time()
    trainer.fit(x_train, y_train,
                train_scorer=lambda w: compute_score(crf_test, w, x_train, y_train_full, relaxed=relaxed_test),
                test_scorer=lambda w: compute_score(crf_test, w, x_test, y_test, relaxed=relaxed_test),
                decompose='grid',
                use_latent_first_iter=use_latent_first_iter, undergenerating_weak=undergenerating_weak,
                smd=smd)
    stop = time()
    time_elapsed = stop - start

    logger.info('testing')

    test_score = compute_score(crf_test, trainer.w, x_test, y_test)
    train_score = compute_score(crf_test, trainer.w, x_train, y_train_full)

    logger.info('========================================')
    logger.info('train score: %f', train_score)
    logger.info('test score: %f', test_score)

    exp_data = {}

    exp_data['timestamps'] = trainer.timestamps
    exp_data['objective'] = trainer.objective_curve
    exp_data['w'] = trainer.w
    exp_data['train_scores'] = trainer.train_score
    exp_data['test_scores'] = trainer.test_score
    exp_data['w_history'] = trainer.w_history

    meta_data['dataset_name'] = 'syntetic'
    meta_data['annotation_type'] = 'full+weak'
    meta_data['label_type'] = 'image-level labelling'
    meta_data['trainer'] = 'komodakis+latent+kappa'
    meta_data['train_score'] = train_score
    meta_data['test_score'] = test_score
    meta_data['time_elapsed'] = time_elapsed

    return ExperimentResult(exp_data, meta_data)


@experiment
def msrc_over(n_train=276, C=100,
              max_iter=1000, check_every=50, verbose=1,
              test_method='gco', test_n_iter=5, relaxed_test=False):
    # save parameters as meta
    meta_data = locals()

    logger = logging.getLogger(__name__)

    crf = HCRF(n_states=24, n_features=2028, n_edge_features=4, alpha=1,
               inference_method=test_method, n_iter=test_n_iter)
    trainer = Over(n_states=24, n_features=2028, n_edge_features=4,
                   C=C, max_iter=max_iter, verbose=verbose, check_every=check_every)

    x_train, y_train, y_train_full, x_test, y_test = \
        load_msrc(n_train, n_train)

    logger.info('start training')

    start = time()
    trainer.fit(x_train, y_train_full,
                train_scorer=lambda w: compute_score(crf, w, x_train, y_train, invert=True, relaxed=relaxed_test),
                test_scorer=lambda w: compute_score(crf, w, x_test, y_test, invert=True, relaxed=relaxed_test))
    stop = time()
    time_elapsed = stop - start

    logger.info('testing')

    test_score = compute_score(crf, trainer.w, x_test, y_test, invert=True, relaxed=relaxed_test)
    train_score = compute_score(crf, trainer.w, x_train, y_train, invert=True, relaxed=relaxed_test)

    logger.info('========================================')
    logger.info('train score: %f', train_score)
    logger.info('test score: %f', test_score)

    exp_data = {}

    exp_data['timestamps'] = trainer.timestamps
    exp_data['objective'] = trainer.objective_curve
    exp_data['w'] = trainer.w
    exp_data['train_scores'] = trainer.train_score
    exp_data['test_scores'] = trainer.test_score
    exp_data['w_history'] = trainer.w_history

    meta_data['dataset_name'] = 'msrc'
    meta_data['annotation_type'] = 'full'
    meta_data['label_type'] = 'full'
    meta_data['trainer'] = 'komodakis'
    meta_data['train_score'] = train_score
    meta_data['test_score'] = test_score
    meta_data['time_elapsed'] = time_elapsed

    return ExperimentResult(exp_data, meta_data)

@experiment
def msrc_over_weak(n_train_full=40, n_train=276, 
                   C=100, alpha=0.1,
                   test_method='gco', test_n_iter=5, n_iter=5,
                   max_iter=1000, verbose=1,
                   check_every=50, complete_every=100, update_w_every=50,
                   relaxed_test=False,
                   use_latent_first_iter=100):
    # save parameters as meta
    meta_data = locals()

    logger = logging.getLogger(__name__)

    crf_test = HCRF(n_states=24, n_features=2028, n_edge_features=4, alpha=alpha,
                    inference_method=test_method, n_iter=test_n_iter)
    crf_latent = HCRF(n_states=24, n_features=2028, n_edge_features=4, alpha=alpha,
                      inference_method='gco', n_iter=n_iter)
    trainer = OverWeak(crf_latent, n_states=24, n_features=2028, n_edge_features=4,
                       C=C, alpha=alpha,
                       max_iter=max_iter, verbose=verbose,
                       check_every=check_every, complete_every=complete_every, update_w_every=update_w_every)

    x_train, y_train, y_train_full, x_test, y_test = load_msrc(n_train_full, n_train, dense=True)

    logger.info('start training')

    start = time()
    trainer.fit(x_train, y_train,
                train_scorer=lambda w: compute_score(crf_test, w, x_train, y_train_full, relaxed=relaxed_test),
                test_scorer=lambda w: compute_score(crf_test, w, x_test, y_test, relaxed=relaxed_test),
                use_latent_first_iter=use_latent_first_iter)
    stop = time()
    time_elapsed = stop - start

    logger.info('testing')

    test_score = compute_score(crf_test, trainer.w, x_test, y_test)
    train_score = compute_score(crf_test, trainer.w, x_train, y_train_full)

    logger.info('========================================')
    logger.info('train score: %f', train_score)
    logger.info('test score: %f', test_score)

    exp_data = {}

    exp_data['timestamps'] = trainer.timestamps
    exp_data['objective'] = trainer.objective_curve
    exp_data['w'] = trainer.w
    exp_data['train_scores'] = trainer.train_score
    exp_data['test_scores'] = trainer.test_score
    exp_data['w_history'] = trainer.w_history

    meta_data['dataset_name'] = 'msrc'
    meta_data['annotation_type'] = 'full+weak'
    meta_data['label_type'] = 'image-level labelling'
    meta_data['trainer'] = 'komodakis+latent+kappa'
    meta_data['train_score'] = train_score
    meta_data['test_score'] = test_score
    meta_data['time_elapsed'] = time_elapsed

    return ExperimentResult(exp_data, meta_data)

#@experiment
#def syntetic_subgrad(n_train=100, mu=1, dataset=1,
#                     max_iter=100, verbose=1):
#    # save parameters as meta
#    meta_data = locals()
#
#    logger = logging.getLogger(__name__)
#
#    crf = HCRF(n_states=10, n_features=10, n_edge_features=2, alpha=1,
#               inference_method='gco', n_iter=5)
#    trainer = Subgrad(model=crf, n_states=10, n_features=10, n_edge_features=2,
#                      mu=mu, max_iter=max_iter, verbose=verbose)
#
#    x_train, y_train, y_train_full, x_test, y_test = \
#        load_syntetic(dataset, n_train, n_train)
#
#    logger.info('start training')
#
#    start = time()
#    trainer.fit(x_train, y_train, lambda w: compute_score(crf, w, x_train, y_train, invert=True))
#    stop = time()
#
#    logger.info('testing')
#
#    test_score = compute_score(crf, trainer.w, x_test, y_test)
#    train_score = compute_score(crf, trainer.w, x_train, y_train)
#
#    logger.info('========================================')
#    logger.info('train score: %f', train_score)
#    logger.info('test score: %f', test_score)
#
#    exp_data = {}
#
#    exp_data['timestamps'] = np.array(trainer.timestamps)
#    exp_data['objective'] = np.array(trainer.objective_curve)
#    exp_data['w'] = trainer.w
#    exp_data['train_scores'] = np.array(trainer.train_score)
#
#    meta_data['dataset_name'] = 'syntetic'
#    meta_data['annotation_type'] = 'full'
#    meta_data['label_type'] = 'full'
#    meta_data['trainer'] = 'mysubgrad'
#    meta_data['train_score'] = train_score
#    meta_data['test_score'] = test_score
#
#    return ExperimentResult(exp_data, meta_data)

@experiment
def syntetic_subgradient(n_train=100, dataset=1, n_jobs=4, C=10,
                         max_iter=100, verbose=1, test_samples=100,
                         check_every=10):
    # save parameters as meta
    meta_data = locals()

    logger = logging.getLogger(__name__)

    crf = HCRF(n_states=10, n_features=10, n_edge_features=2, alpha=1,
               inference_method='gco', n_iter=5)
    clf = SubgradientSSVM(crf, verbose=verbose, n_jobs=n_jobs,
                         max_iter=max_iter, C=C, check_every=check_every)

    x_train, y_train, y_train_full, x_test, y_test = \
        load_syntetic(dataset, n_train, n_train)
    x_test1 = x_test[:test_samples]
    y_test1 = y_test[:test_samples]

    logger.info('start training')

    start = time()
    clf.fit(x_train, y_train_full,
            train_scorer=lambda w: compute_score(crf, w, x_train, y_train),
            test_scorer=lambda w: compute_score(crf, w, x_test1, y_test1))
    stop = time()

    logger.info('testing')

    test_score = compute_score(crf, clf.w, x_test, y_test)
    train_score = compute_score(crf, clf.w, x_train, y_train)

    logger.info('========================================')
    logger.info('train score: %f', train_score)
    logger.info('test score: %f', test_score)

    exp_data = {}

    exp_data['w'] = clf.w
    exp_data['objective'] = np.array(clf.objective_curve_)
    exp_data['train_scores'] = np.array(clf.train_scores)
    exp_data['test_scores'] = np.array(clf.test_scores)
    exp_data['timestamps'] = np.array(clf.timestamps_)
    exp_data['w_history'] = clf.w_history

    meta_data['dataset_name'] = 'syntetic'
    meta_data['annotation_type'] = 'full'
    meta_data['label_type'] = 'full'
    meta_data['trainer'] = 'subgradient'
    meta_data['train_score'] = train_score
    meta_data['test_score'] = test_score

    return ExperimentResult(exp_data, meta_data)

#binary exp

@experiment
def binary_full_fw(n_train=100, C=1, dataset=1,
                   max_iter=1000, n_inference_iter=5,
                   check_dual_every=10, test_samples=100,
                   inference_method='gco'):
    # save parameters as meta
    meta_data = locals()

    logger = logging.getLogger(__name__)

    crf = HCRF(n_states=2, n_features=10, n_edge_features=1, alpha=1,
               inference_method=inference_method, n_iter=n_inference_iter)
    clf = FrankWolfeSSVM(crf, verbose=2, n_jobs=1, check_dual_every=check_dual_every,
                         max_iter=max_iter, C=C)

    x_train, y_train, x_test, y_test = \
        load_binary_syntetic(dataset, n_train)

    logger.info('start training')

    start = time()
    clf.fit(x_train, y_train, Xtest=x_test[:test_samples], Ytest=y_test[:test_samples])
    stop = time()

    train_score = clf.score(x_train, y_train)
    test_score = clf.score(x_test, y_test)
    time_elapsed = stop - start

    logger.info('============================================================')
    logger.info('Score on train set: %f', train_score)
    logger.info('Score on test set: %f', test_score)
    logger.info('Elapsed time: %f s', time_elapsed)

    exp_data = {}

    exp_data['timestamps'] = clf.timestamps_
    exp_data['primal_objective'] = clf.primal_objective_curve_
    exp_data['objective'] = clf.objective_curve_
    exp_data['w_history'] = clf.w_history
    exp_data['test_scores'] = clf.test_scores
    exp_data['train_scores'] = clf.train_scores
    exp_data['w'] = clf.w

    meta_data['dataset_name'] = 'syntetic binary'
    meta_data['annotation_type'] = 'full'
    meta_data['label_type'] = 'full'
    meta_data['trainer'] = 'frank-wolfe'
    meta_data['train_score'] = train_score
    meta_data['test_score'] = test_score
    meta_data['time_elapsed'] = time_elapsed

    return ExperimentResult(exp_data, meta_data)


@experiment
def binary_over(n_train=100, C=1, dataset=1,
                max_iter=100, verbose=1,
                test_samples=100, check_every=10,
                test_method='gco', test_n_iter=5, relaxed_test=False):
    # save parameters as meta
    meta_data = locals()

    logger = logging.getLogger(__name__)

    crf = HCRF(n_states=2, n_features=10, n_edge_features=1, alpha=1,
               inference_method=test_method, n_iter=test_n_iter)
    trainer = Over(n_states=2, n_features=10, n_edge_features=1,
                   C=C, max_iter=max_iter, verbose=verbose, check_every=check_every)

    x_train, y_train, x_test, y_test = \
        load_binary_syntetic(dataset, n_train)
    x_test = x_test[:test_samples]
    y_test = y_test[:test_samples]

    logger.info('start training')

    start = time()
    trainer.fit(x_train, y_train,
                train_scorer=lambda w: compute_score(crf, w, x_train, y_train, invert=True, relaxed=relaxed_test),
                test_scorer=lambda w: compute_score(crf, w, x_test, y_test, invert=True, relaxed=relaxed_test))
    stop = time()
    time_elapsed = stop - start

    logger.info('testing')

    test_score = compute_score(crf, trainer.w, x_test, y_test, invert=True, relaxed=relaxed_test)
    train_score = compute_score(crf, trainer.w, x_train, y_train, invert=True, relaxed=relaxed_test)

    logger.info('========================================')
    logger.info('train score: %f', train_score)
    logger.info('test score: %f', test_score)

    exp_data = {}

    exp_data['timestamps'] = trainer.timestamps
    exp_data['objective'] = trainer.objective_curve
    exp_data['w'] = trainer.w
    exp_data['train_scores'] = trainer.train_score
    exp_data['test_scores'] = trainer.test_score
    exp_data['w_history'] = trainer.w_history

    meta_data['dataset_name'] = 'syntetic binary'
    meta_data['annotation_type'] = 'full'
    meta_data['label_type'] = 'full'
    meta_data['trainer'] = 'komodakis'
    meta_data['train_score'] = train_score
    meta_data['test_score'] = test_score
    meta_data['time_elapsed'] = time_elapsed

    return ExperimentResult(exp_data, meta_data)


@experiment
def binary_cp(n_train=100, C=1, dataset=1,
              max_iter=1000, n_inference_iter=5,
              check_dual_every=10, test_samples=100,
              inference_method='gco'):
    # save parameters as meta
    meta_data = locals()

    logger = logging.getLogger(__name__)

    crf = HCRF(n_states=2, n_features=10, n_edge_features=1, alpha=1,
               inference_method=inference_method, n_iter=n_inference_iter)
    clf = OneSlackSSVM(crf, verbose=2, n_jobs=4,
                            max_iter=max_iter, C=C)

    x_train, y_train, x_test, y_test = load_binary_syntetic(dataset, n_train)

    logger.info('start training')

    start = time()
    clf.fit(x_train, y_train,
            train_scorer=lambda w: compute_score(crf, w, x_train, y_train, invert=False),
            test_scorer=lambda w: compute_score(crf, w, x_test, y_test, invert=False))
    stop = time()

    train_score = clf.score(x_train, y_train)
    test_score = clf.score(x_test, y_test)
    time_elapsed = stop - start

    logger.info('============================================================')
    logger.info('Score on train set: %f', train_score)
    logger.info('Score on test set: %f', test_score)
    logger.info('Elapsed time: %f s', time_elapsed)

    exp_data = {}

    exp_data['train_scores'] = clf.train_scores
    exp_data['test_scores'] = clf.test_scores

    meta_data['dataset_name'] = 'syntetic binary'
    meta_data['annotation_type'] = 'full'
    meta_data['label_type'] = 'full'
    meta_data['trainer'] = 'cutting plane'
    meta_data['train_score'] = train_score
    meta_data['test_score'] = test_score
    meta_data['time_elapsed'] = time_elapsed

    return ExperimentResult(exp_data, meta_data)
